# Code review — ticket 06, paired honest-instruction columns

**Fixed point:** `a74d54b` (the `component-analysis` tip at the start of block D).
**Branch:** `ca/06-paired-honest-columns`.
**Reviewed at:** `c7b4d37` (first pass) and `a74d54b...57bbf24` (second pass, both
commits). Three commits follow — `e1a8520`, `6d1c5dd` and `07bbe43` — and the
disposition table says which findings each closes. Branch tip `07bbe43`.

**How the review was run.** `mattpocock-skills:code-review` against `a74d54b`,
both axes as parallel sub-agents. Both delivered — late, by way of the
orchestrator rather than back to the author, as happened on tickets 02, 02b and
04. **This review is independent of the author.** Both agents' reports are
reproduced verbatim below, followed by the disposition of every finding.

An author's own two-axis pass had been written into this file before the
sub-agents' reports arrived; where it found the same thing the independent
reports found, the independent wording is the one kept.

---

## Standards — the reviewer's report, verbatim

> Pairing rule verified (`honest_instruction_slices` counts misalignment into
> `report` without dropping rows). interp-tooling.md not load-bearing (no nnsight
> code in the diff); the module-import probe guards the rule.
>
> **HARD — tests assert below the caller's seam.** Repo rule: "Tests assert at
> seams the caller sees (written files, returned numbers), never hook wiring or
> intermediate tensors." tests/test_paired_honest.py,
> test_the_paired_pressure_side_carries_the_pressure_prompt_not_the_honest_one:
> `assert pressure.input_ids.tolist() == batches[0].input_ids[[1]].tolist()`
> Tensors from an internal generator; the docstring names the target as "the
> obvious bug: yielding batch.honest.input_ids twice" — wiring. Same for the two
> neighbouring `*_slices` tests. Tension to surface, not resolve: the file-seam
> equivalent (test_both_sides_of_the_pair_are_profiled_over_the_same_instances)
> is in the nnsight-0.7.0-gated CLI file, so on the login node these are the only
> coverage.
>
> **HARD-ish (57bbf24) — the JSON twin no longer describes the figure.**
> plot_paired_scatter's own docstring: "Drawn from the JSON twin... whatever a
> reader finds in the file is what was plotted." The new zoom_limit/two-panel
> split and the cut value exist only in the PNG; dla_paired_scatter.json has no
> `zoom` or panel field, so a reader of the file cannot tell the picture has two
> panels or where it cuts. Put the zoom limit and the panel membership in the
> twin's meta.
>
> **Caller-visible misstatement — attention_patterns.estimate:**
> `parts.append(line("honest-instruction (paired), both sides:", 2 * len(causal), ...))`
> `line` renders arg 2 as "in {n_batches} batch(es)", so --dry-run prints a false
> batch count. Double `forwards` inside _cost, or add passes=.
>
> Judgement calls:
> - **Middle Man + Mysterious Name (57bbf24):** `def ap_dla_zoom(points): return
>   dla.zoom_limit(points)` — a one-line pass-through, defined after its three
>   call sites, with an `ap_` prefix naming the wrong module. Call dla.zoom_limit
>   directly.
> - **Boundary double-label:** _scatter_panel uses `label_from <= mag <= limit`
>   inclusive on both ends, so a Component exactly at `zoom` is named in both
>   panels and `named + shown` exceeds len(points), contradicting "the two panels
>   divide the labels between them".
> - **Duplicated Code:** the literal (PRESSURE_PAIRED, HONEST_INSTRUCTION)
>   appears three times in dla.py (paired_scatter_payload's by_key,
>   paired_lens_conditions, paired_lens_figure_payload) — wants a
>   PAIRED_CONDITIONS constant. Separately PRESSURE/HONEST_INSTRUCTION/
>   HONEST_TWIN/CONDITIONS/PRESSURE_PAIRED and wanted_conditions are each defined
>   twice, once per module; ap.wanted_conditions calls divergence "a trap" but
>   guards it by copy-paste (registry.py's sibling-branch rationale plausibly
>   justifies it).
> - **paired_lens_payload (JSON) and paired_lens_figure_payload (PNG)** derive the
>   lens twice from the same source and can drift — the opposite of the rule the
>   scatter states.
> - **Mysterious Name:** test_paired_honest_cli.py uses `twin` for the Honest Twin
>   dataset and `twin` for a JSON-twin-of-figure; CONTEXT.md owns "Twin".
> - **Late validation:** the renamed test's new docstring concedes "a real run
>   validates the flag inside run(), after the model is loaded" — an invalid
>   --attention-conditions burns a GPU load before failing, unlike registry.select
>   which refuses unknown names up front.
>
> Nits: `wanted = COLUMN_PREFIXES` alias is vestigial; build_sdr_split imported
> unused under blanket noqa: E402,F401;
> test_the_paired_lens_twin_says_why_it_is_empty(tmp_path) never uses tmp_path.
>
> Clean: pairing rule holds (honest_instruction_slices only counts misalignment
> into `report`, drops no rows, so both sides carry the same ids); CONTEXT.md
> vocabulary, no avoided terms; _descriptive marking on unpaired twin columns;
> bare unprefixed head-table column names; every figure has a JSON twin; sign
> convention carried via METRIC. No nnsight import at module scope, and
> test_this_module_pair_does_not_import_nnsight guards it. Registry's five-name
> rule says "required", so extra public helpers are house style, not a breach.

## Spec — the reviewer's report, verbatim

> Spec-axis review of a74d54b...57bbf24 (both commits): no blocking defects; four
> findings, all low/non-blocking.
>
> Re-checked the new commit 57bbf24 ("Give the paired scatter a second panel"). It
> is within ticket 06's "paired DLA scatter (pressure vs honest) with Components
> labelled" — a single panel scaled to the outlier MLP leaves most labels
> illegible, so the two-panel split serves the requirement rather than exceeding
> it. `zoom_limit` is correct: magnitudes sorted ascending, the loop starts at
> ZOOM_MIN_INSIDE-1 so at least two Components stay inside the cut, and it returns
> None when the best ratio gap is under 4x. The two panels' label ranges ([zoom,
> full] and [0, zoom]) cover every point, so the docstring's "no Component goes
> unnamed" holds. `Sequence`/`Optional` are imported (dla.py:91).
>
> Pairing check (the thing you asked me to scrutinise): **correct.**
> `attention_patterns.paired_rows` is the single row selector for both paired
> conditions; `pressure_paired_slices` yields `batch.input_ids[rows]` and
> `honest_instruction_slices` yields `batch.honest.input_ids[keep]` for the same
> `rows`, so `pressure_paired` genuinely reads the same instance ids as
> `honest_instruction`. Satisfies block C's "'paired' columns are computed over
> the same instance ids on both sides".
>
> **(a) Missing or partial**
> 1. **Slurm verification unmet.** Ticket checkbox: "Verified by a short Slurm run
>    on SDR; differential column non-trivial for at least some Components." No
>    evidence anywhere; the ticket file still has every box unticked, no
>    `## Comments`, `**Status:** claimed`. Blocks `resolved`, not merge.
> 2. **The attention JSON records no per-condition `instance_ids`**, while
>    dla.py:941 does. Spec US 28: "causal analyses over a fixed-seed sample of one
>    hundred instances whose ids are recorded"; US 43 wants every result
>    agent-readable. Consequence:
>    `test_both_sides_of_the_pair_are_profiled_over_the_same_instances` can only
>    assert equal per-level `n`, not equal ids, so the pairing property is
>    guaranteed by code path rather than at the seam Testing Decisions names
>    ("asserts external behaviour at a seam the caller sees"). Recommend mirroring
>    dla.py's `instance_ids`.
> 3. **The paired descriptive columns are computed over the N=100 causal sample,
>    not the split.** Spec Implementation Decisions, Sampling: "Descriptive
>    analyses use the full test split." Inherited from ticket 04 (its Comments:
>    "71 of the 100 sampled on SDR") and researcher-visible there, so I read it as
>    accepted rather than lost in the shrink — flagged so nobody reads
>    `honest_instruction_top_segment` as a full-split number.
>
> **(b) Scope creep — minor only.** Spec says "Three condition columns: pressure,
> honest-instruction (paired), honest twin (unpaired, marked descriptive)"; the
> diff writes four, adding `pressure_paired`. Justified by the block C rule and
> ticket 04's `dla.pressure_paired` precedent — a documented deviation, not creep.
> Genuine minor: `--attention-conditions` lets `pressure` itself be dropped,
> whereas `dla` re-raises when the pressure loader is missing; the two sibling
> flags now differ in strictness with nothing saying why.
>
> **(c) Implemented but questionable — naming.** The scheme marks unpaired columns
> with `_descriptive` and leaves paired ones bare, so a CSV reader can separate
> `honest_instruction_*` from `honest_twin_descriptive_*`. But bare
> `pressure_top_segment` / `dla.pressure` is also unpaired and unmarked, so
> `pressure` vs `honest_instruction` remains a population contrast a header will
> not warn about — the exact trap US 27 targets. attention_patterns.py's own
> comment admits it. Inherited block C convention; note it, do not block on it.
>
> Deliverables present and correct: `--attention-conditions` (analysis-prefixed),
> the paired attention column plus top Segment under the honest instruction,
> `dla/dla_paired_scatter.{png,json}`, `dla/logit_lens_paired.{png,json}`
> overlaying only the two paired conditions, empty-figure paths that state their
> reason, and a CLI-seam test on a synthetic paired dataset with a Matched Honest
> pool and survivors file.

---

## Disposition of every finding

The orchestrator ruled on each; its calls are followed except where noted.

| # | Axis | Finding | Outcome |
|---|---|---|---|
| 1 | Standards, caller-visible | `estimate` printed a false batch count: 26 where the loader has 13. | **Fixed** in `e1a8520`, which predates the reports — the author's own pass found the same thing. `line(..., passes=2)` prints "13 batch(es) read 2x"; the forward count and the timing were already right and are unchanged. Re-rehearsed with `--dry-run`. |
| 2 | Standards, hard-ish | The scatter's JSON twin did not describe the two-panel figure: no `zoom`, no panel membership. | **Fixed.** The twin gains `zoom`, a `panels` note, and a `panel` field per point (`full`, `zoom` or `single`). The plotter now **reads** the panel assignment off the twin instead of recomputing it, so the file's account is the figure's account. |
| 3 | Standards, judgement | Boundary inclusive on both ends, so a Component exactly at the cut is named in both panels and the two counts can exceed the number of Components. | **Fixed.** `panel_of` is half-open: `magnitude < zoom` goes to the zoom panel, everything else to the full one. A test pins the boundary case and a second pins that the two panels name every Component exactly once. |
| 4 | Standards, judgement | `ap_dla_zoom` — a one-line pass-through named for the wrong module, defined after its call sites. | **Fixed.** Deleted; the tests call `dla.zoom_limit` directly. |
| 5 | Standards, judgement | `(PRESSURE_PAIRED, HONEST_INSTRUCTION)` spelled three times in `dla.py`. | **Fixed.** `dla.PAIRED_CONDITIONS`, used by the scatter's axes, the lens twin and the lens figure. A test asserts the scatter's `(x, y)` and the lens twin's condition set are both that constant. |
| 6 | Standards, judgement | `paired_lens_payload` (JSON) and `paired_lens_figure_payload` (PNG) derived the lens twice from one source and could drift — the opposite of the rule the scatter states. | **Fixed.** `paired_lens_figure_payload` now takes the **twin** and reshapes it into what `plot_lens` reads, so the PNG is drawn from the file. The test edits the twin and asserts the edit reaches the figure payload. |
| 7 | Standards, judgement | `twin` means both the Honest Twin dataset and a figure's JSON twin in one test file; CONTEXT.md owns "Twin". | **Fixed.** The dataset is `honest_twin` / `honest_twin_dir`; each figure's companion is `scatter` or `lens` at its point of use. |
| 8 | Standards, judgement | Late validation: an invalid `--attention-conditions` burned a GPU load before failing, unlike `registry.select`. | **Fixed** in `6d1c5dd` and `07bbe43`. `parse_conditions` is the flag's `type=`, so argparse refuses an unknown name at parse time — before the circuits resolve and before any model loads. The test asserts `SystemExit(2)` on a **real** run, not a dry run. `07bbe43` follows because the first fix silently cost the message: argparse discards a plain `ValueError`'s text and printed "invalid parse_conditions value: 'honest'", naming the function rather than the flag and listing nothing, so `UnknownCondition` subclasses both `ValueError` and `argparse.ArgumentTypeError`. **`--dla-conditions` was deliberately left alone**: it is ticket 04's, its existing test asserts `ValueError` from inside `run`, and changing it would alter shipped behaviour this ticket was not asked to touch. The two flags now differ in *when* they reject a typo, which is recorded in the ticket. |
| 9 | Standards, hard | Three `*_slices` tests assert on tensors from an internal generator, below the caller's seam. | **Kept, on the orchestrator's condition**, which was met: a seam-level assertion that both sides' recorded `instance_ids` are equal now exists in the CLI file (finding 11 made it possible). The three stay, with the reason written into the file above them: the seam-level form needs a model and so does not run on the login node at all, and the specific bug they catch — yielding the honest prompt for both sides — produces a **well-formed** `patterns.json` with matching ids, matching counts and every paired difference exactly zero. That reads as a finding, not a failure. Only the prompts distinguish the two. |
| 10 | Spec (a1) | Slurm verification unmet; ticket unticked, no Comments, status claimed. | **Done**, after the reviewers took their snapshot. Job `22123694`, A40, 10:45, COMPLETED. Re-run after these fixes, because the JSON schema changed. Numbers in the ticket. |
| 11 | Spec (a2) | The attention JSON recorded no per-condition `instance_ids`. | **Fixed.** `collect_condition` collects them and `_condition_json` writes them as the condition's own field. This is what turned finding 9 from an argument into a fix. |
| 12 | Spec (a3) | Paired descriptive columns run over the N=100 causal sample, not the full split. | **Documented, not changed.** Inherited from ticket 04 and accepted by the orchestrator. It is inherent to a paired counterfactual — only the survivors of the Matched Honest filter have one — and `patterns.json` records `n_instances` and `n_loaded` separately. Ticket open question 3 puts it in front of the researcher. |
| 13 | Spec (b) | `--attention-conditions` lets `pressure` be dropped; `dla` re-raises when the pressure loader is missing. The two sibling flags differ in strictness with nothing saying why. | **Documented.** The flag's help now says dropping `pressure` is allowed and leaves the cell with no full-split column, "a smoke-run shape, not a reporting one". Aligning the two flags means changing ticket 04's behaviour; not done here. |
| 14 | Spec (c) | Bare `pressure_top_segment` and `dla.pressure` are unpaired and unmarked, so `pressure` versus `honest_instruction` is still a population contrast no header warns about. | **Not changed; this is the live open question.** It is ticket 04's open question 2, inherited block C convention, and the reason `pressure_paired` exists at all: the paired column now *has* a correctly paired left term to be read against, which is the part this ticket could fix without renaming shipped columns. Carried to the researcher as ticket open question 1. |
| 15 | Standards, nits | Vestigial `wanted = COLUMN_PREFIXES` alias; unused `build_sdr_split` import under a blanket `noqa`; unused `tmp_path`. | **All three fixed.** |
| 16 | Standards, judgement | The condition constants and `wanted_conditions` are defined twice, once per module. | **Kept.** `registry.py`'s own docstring gives the reason — sibling branches rebasing onto one list — and the two copies are each the module's own vocabulary rather than a shared one. Recorded. |
| 17 | Standards, judgement | The heatmap now has four panels rather than three. | **Kept.** Every panel carries its own `n` and `paired` flag and the JSON twin carries the same matrices. Flagged for the researcher. |
| 18 | Standards, judgement | The condition-gating idiom repeats three times in `run` and twice in `estimate`. | **Kept.** The three branches call three different functions returning three different shapes, so a helper would have to unify them first. Author's finding, not the reviewers'. |

---

## Summary

- **Standards: 3 hard or caller-visible findings, all fixed** (1, 2, 8 — counting
  late validation, which the orchestrator escalated); **9 judgement calls, 5 fixed
  and 4 kept with reasons**; 3 nits, all fixed. Finding 9 is kept rather than
  fixed, on the orchestrator's stated condition, which was met.
- **Spec: 0 blocking defects. 2 findings fixed** (11, and 10 by doing the run),
  **3 documented** (12, 13, 14). No requirement in the shrunken scope is
  implemented incorrectly.
- **Worst within Standards:** finding 2 — a figure whose JSON twin does not
  describe it breaks the rule that makes every result agent-readable, and the
  docstring claimed the opposite.
- **Worst within Spec:** finding 14 — the column headers still do not warn that
  `pressure` and `honest_instruction` are different populations. It cannot be
  fixed inside this ticket without renaming columns the researcher has outputs
  for, and it is the first thing the ticket asks them to decide.
