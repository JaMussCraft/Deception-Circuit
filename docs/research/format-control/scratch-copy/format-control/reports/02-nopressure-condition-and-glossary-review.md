# Ticket 02 review: `nopressure` condition and glossary

Reviewer: independent review subagent, 2026-10-13.
Diff: 5b61031..e194874 on `format-control-02` (c1c1f39, e194874).
Read-only review. I read the diff once. Outside the diff I checked four named risks:

- Every remaining enumeration of `"honest"` / `_honest` in `evaluation/`, `tasks/`, `scripts/`, `dataset/`, `run_io.py`, `train.py` and `evaluate_circuit.py`.
- How `CircuitSpec.operands` is populated for atomic, composed and legacy circuits.
- How the joint task reaches the dataset directory.
- Whether anything parses the `suite.log` banner lines whose format changed.

I re-ran no tests.

## Spec Compliance

- ✅ **`dataset_dir`.** `tasks/deception.py:27-35` maps `deceptive` to `<task>` and every other registered condition to `<task>_<condition>`, with no literal per-condition branch. `tasks/joint_deception.py:74,146` goes through the same method, so joint inherits it. Unknown conditions now raise.
- ✅ **One enumeration.** `tasks/__init__.py` defines `DECEPTION_CONDITIONS`, and `train.py` takes its `choices` from it. The grep found no other condition enumeration in `evaluation/`, `tasks/` or `run_io.py`. The remaining `"honest"` hits are in `knockout.py`, `benchmark_eval.py` and `benchmarks/`, and they name behaviour verdicts, not dataset conditions. `dataset/deception_comparison_set.py:32,42` still offers only deceptive/honest. That file is outside the ticket's named locations, and the report explains why it was left alone.
- ✅ **Slug.** `run_io.py:136-142` appends any non-deceptive condition at the position `honest` used. The end-to-end test asserts `..._nls0.3_nopressure_noedge_<stamp>` with `fullmatch`. The unit test asserts the `nls0.3_{,honest_,nopressure_}noedge_` prefixes, so the honest slug is unchanged.
- ✅ **Config and `--task-from`.** `run_io.py:87` already records `deception_condition`. `_RUN_CONFIG_KEYS` and `_DATASET_KEYS` already carry it. The test `test_task_from_a_nopressure_run_resolves_the_nopressure_test_set` checks four things: the resolved args, the provenance, `dataset_dir` returning `far_nopressure`, and the loader yielding the 4 no-pressure records rather than the 6 deceptive ones. The loader check is the strong one.
- ✅ **Runtime filter and margin loss.** Neither path has a condition branch. Tests cover the dataset `margin_thresh` default of 0.5, the 0.25 override, and the filter on and off at margin 1000. With the filter, val/test go from 4 records to 0 while train stays at 4.
- ✅ **Help text.** The `train.py` help text and module docstring both name the Format Circuit. A test asserts "Format Circuit" appears in `--help`.
- ✅ **Condition printing.** `evaluate_circuit.py:689-697` adds a condition to the dry-run CIRCUITS and TASKS lines. `evaluation/suite.py:333-341` adds it to the suite banner. The report interprets "suite summary" as the banner and the dry-run plan, because `evaluation_summary.md` is ticket 05's. That reading is reasonable, and the helpers are importable for ticket 05.
- ✅ **CONTEXT.md.** The **Format Circuit** entry sits under `### Task structure`, after **Honest Twin**, with the ticket's wording and _Avoid_: control circuit, template circuit. **Honest Condition** gains the Twin-vs-`nopressure` note, and its _Avoid_ still lists "control". **Pressure Clause** gains one sentence so that its "present in both conditions" claim no longer contradicts the new condition. "control" appears only in _Avoid_ lines.
- ✅ **Forbidden files untouched.** The diff stat does not include `evaluation/variants.py`, `dataset/deception_common.py`, `dataset/build_*` or `tests/test_variants.py`.
- ✅ **Required tests are present.** They cover `dataset_dir` for all three conditions, `train.py` parsing `nopressure`, an end-to-end tiny-Llama training run writing `deception_condition: "nopressure"`, and `--task-from` resolving the `_nopressure` set.
- ⚠️ **Suite results cannot be verified from the diff.** The report says both envs show 8 failures, matching the baseline names exactly. The full suites ran at c1c1f39, not at head e194874. e194874 adds only one characterisation test, which was run on its own file in both envs. That is acceptable, because the commit touches no production code. The report includes no warning or noise output, so I cannot say whether the new tests emit warnings, for example from `datasets` `save_to_disk` or the transformers eager-attention notice.

## Strengths

- **One code path for every non-deceptive condition.** `dataset_dir`, the slug and the condition printers have no `nopressure` literal. This directly meets "no special casing", and a future condition needs only an entry in `DECEPTION_CONDITIONS`.
- **Unknown conditions fail loudly.** `dataset_dir` used to send any unrecognised string to the deceptive directory without a warning. It now raises. The test uses the plausible typo `no_pressure`, which is exactly the spelling `PROMPT_VARIANTS` uses.
- **Tests that tell the datasets apart.** The 6-record versus 4-record datasets and the 1.0 versus 0.5 margins mean a test passes only if the right directory was actually read.
- **Banner shows each operand's condition.** A label like `D:deceptive,F:nopressure` makes delta cells such as `D-F` self-describing in the log.
- **Additive edits to shared files.** `CircuitSpec` and `TaskSpec` are unchanged, which keeps conflicts with tickets 04 and 05 small.

## Issues

### Critical

None.

### Important

None.

### Minor

1. **`train.py:126-131` help text is stale.** It still ends "The comparison unit is Δ = C_deceptive − C_honest, so both are trained." With three choices, "both" no longer fits, and the sentence suggests `nopressure` is part of that difference. A fix: "The comparison unit is Δ = C_deceptive − C_honest; the nopressure run is the Format Circuit control for both."

2. **The condition-defaulting idiom appears three times.** `getattr(args, "deception_condition", None) or "deceptive"` is repeated at `tasks/deception.py:30` and `run_io.py:140`, and as `get(...) or "deceptive"` in `evaluation/circuits.py:252`. If the default ever changes, three places must agree. A small helper in `tasks/__init__.py`, for example `deception_condition(args_or_config)`, could serve all three, and `condition_of` would wrap it. This is polish, not a correctness problem.

3. **`evaluation/circuits.py:240-252` `condition_of` duck-types its input.** It accepts either a dict or an attribute object through an inline lambda. It works, but two thin entry points, or normalising with `vars(ns)` at the call sites, would read more plainly.

4. **The fixture's `nopressure` records are not really no-pressure.** At `tests/test_nopressure_condition.py:71-74`, the records set `condition="nopressure"` and `pressure=""`. They keep the deceptive prompts, with the clause still in the text, and the deceptive target/distractor order. That is fine for a plumbing test, and the module docstring says so. However, the fixture comment and the CONTEXT.md entry both describe "clause deleted, honest labels". A one-line comment saying the prompts are deliberately not rewritten would stop a later reader from reusing this fixture as a realistic no-pressure sample.

5. **The glossary uses "template circuit" in two senses.** CONTEXT.md **Template Variant** (around line 96) uses "template circuit" in its own sense: a circuit that tracks surface phrasing, in the variance decomposition. The new Format Circuit entry lists "template circuit" under _Avoid_. The ticket mandated that _Avoid_ list, so this is not a defect of the implementation. It is a terminology tension worth one clarifying word, for example "_Avoid_: control circuit, template circuit (that names the phrasing effect under **Template Variant**)".

6. **A composed circuit on a task without conditions prints dashes.** `circuit_condition` for a composed circuit on such a task, for example std, prints `A:-,B:-`. This is harmless but noisy. It could collapse to `-` when every operand returns `-`.

7. **The new `evaluation/circuits.py` import in `suite.py` adds a module dependency.** `evaluation/suite.py:41` now imports `evaluation.circuits`, which imports `evaluation.context` and `evaluation.algebra`. No cycle exists today, and the suites passed. Keep it in mind if ticket 04 or 05 makes `circuits` import `suite`.

## Assessment

**Task quality: Approved.** The change makes `nopressure` a registered condition handled by the same code path as `honest`, from training, slug and config through `--task-from` and the evaluator. Tests prove the right directory and margin are actually read. CONTEXT.md meets the ticket's wording. All findings are Minor polish, and the stale "so both are trained" help text is the one worth fixing before merge.
