# Ticket 05 implementer report: format-control summary writer and decision rule

Date: 2026-10-13. Implementer: impl-05. Worktree `Deception-Circuit/.claude/worktrees/format-control`,
branch `format-control`, base e439e91.

## Status: DONE_WITH_CONCERNS (build phase; the real-suite run awaits ticket 04's cells)

All boxes are ticked except two. "Run on the three real suites" awaits ticket 04's merged cells.
"Independent review" is the orchestrator's to dispatch. **Commits are made by the orchestrator on my
instruction.** I sent the commit request with the file list and message; I ran no git command.

## What was built

| path | what |
| --- | --- |
| `evaluation/format_control_summary.py` | library: `summarize`, `decide` (pure), `render`, `decision_record`, `write_summary` |
| `write_format_control_summary.py` | CLI at the repo root, like `compare_node_masks.py` |
| `tests/test_format_control_summary.py` | 29 tests on fixture suites the test writes (fine and coarse), plus an eval 5 fixture |

The library is stdlib only. It does not import `evaluation.circuits` or `evaluation.variants`,
because both pull in torch. Instead it reads `config.json` directly, mirroring `condition_of`, and
implements the `LABEL_CONVENTION` semantics in code. The check `import evaluation` loads no torch.

**Inputs.** Each input is read from the following source:
- Cells come from `cells/<label>/<dataset dir>/interchange/{knockout,null,sanity,summary}.json`.
  - In a fine suite, the knockout for circuit X is the atomic cell `X`.
  - In a coarse suite, the knockout is the `X_hko__leaf` cell and the sufficiency is the `X` cell.
  - Delta cells are `<label>__{head,leaf}` (fine) or `<label>_hko__leaf` (coarse).
- `suite.json` supplies run dirs (`home_run_dir` / `operands`) and delta head counts. Counts may be ints or `{active, total}` dicts.
- `overlap.json` and `flip_audit.json` come from the suite root. The flip audit's `positional.verdict` and `headline.separable` are joined per cell.
- `data/datasets/<task>_nopressure/dataset_config.json` `source_counts` gives the pairing. The data-dir is set with `--data-dir`.
- Each run's `config.json` gives the condition, NLS and `deception_margin_loss`. When `size_check.json` sits beside F, its `format_nls` overrides.
- Eval 5 comes from `--eval5-dir` (repeatable). The writer reads `<dir>/cells/<circuit>/<task>/<ablation>/benchmarks.json`. Circuit labels map to roles after stripping `__leaf`, `__head` and `_hko`.

**Full-model accuracy is shared down each dataset column.** Delta and coarse `_hko` cells run eval 2
only and carry no full row. The writer therefore takes the column's value from any cell on that
dataset: `null.json anchors.full`, else `sanity.json rows.full_open`.

**Outputs.** `evaluation_summary.md` contains:
- a header with each circuit's condition, NLS and run dir, and each dataset's condition, full accuracy and paired flag;
- the decision block;
- the paired table, one sub-table per dataset column;
- the variant honest-answer rows;
- the eval 5 table, only when a directory is given;
- the overlap table;
- the delta rows, with head primary for fine suites and "head (composed at leaf)" for coarse;
- caveats, decisions taken, and the missing section.

`decision.json` carries the verdict, the spec sentence, every condition with its inputs and
pass/fail, the gate, the rule order, the decisions taken, the thresholds, the run conditions, the
pairing, the caveats and the missing lists.

## The rule as encoded

The verdict is reached in this order:
- **(c) first:** F's knockout has wikitext KL/token > 0.66, or a distinct-2 collapse.
- **(a):** all four conditions pass.
  - The deception drop on D data satisfies F >= 0.8 x D. The comparison has a 1e-9 tolerance, which decides the exact-80 percent case.
  - The honest-answer drop satisfies F <= D on every row: honest_instruction and no_pressure on D data, the H test set, and the F test set.
  - Collateral satisfies F <= D. The measure is the eval 5 reference-NLL rise when given, else the eval 2 wikitext KL.
  - Both knockouts are strictly below their own null's 5th percentile.
- **(b):** any condition fails.
- **Undecided:** a rule input is missing, the gate did not fire, and no other condition failed. A failed condition with a missing input gives (b), with the input still listed. A test pins this.

## Decisions I took that the researcher may want to revisit

**Orchestrator ruling, 2026-10-13.** Decisions 1 and 4 below stand. Both outputs now label them
"not pre-registered; orchestrator choice 2026-10-13, researcher to confirm". The label appears in
the rule order, the (c) gate line, `gate.distinct2_frac_status` and `decisions_taken`. A test pins
it, and the summary test file is 35 of 35 in the base env.

1. **(c) is checked before (a).** The spec says "Anything else is (b), unless F is also incoherent".
   Read literally, (c) overrides only (b). I check (c) first. Otherwise an F that passes "KL <= D's"
   only because D is itself above 0.66 could read as (a).
2. **Honest-answer drop is compared row by row.** F must not exceed D on any of the four rows. The
   spec's singular "honest-answer drop" needs some aggregate, and this one is strict.
3. **The sign on D-data variant rows.** The rows keep deceptive labels (`LABEL_CONVENTION`), so the
   honest-answer drop there is knockout minus full. The real FAR D x far honest_instruction row
   gives 0.861 - 0.106 = 0.755. The cell's own `headline.honest_accuracy_drop` is -0.755, the
   opposite sign, and the writer does not use it.
4. **Distinct-2 collapse threshold.** The threshold is 0.5 x the full model's distinct-2. The spec
   names no number. Without eval 5, the writer computes word-bigram distinct-2 over eval 2's three
   48-token wikitext continuations. That is a weak proxy, and eval 5 `distinct_n` replaces it when
   given.
5. **Eval 5 changes only collateral and the distinct-2 source.** Collateral uses the mean
   reference-NLL rise over benchmark datasets. The deception drop stays eval 2's task drop, per the
   orchestrator's fact. The benchmark deception-rate drop is shown but does not enter the rule.
6. **Missing inputs.** A missing rule input gives "undecided" with the inputs named. Two cases
   still decide: the (c) gate can fire on its own, and an already failed condition gives (b).

Delta head counts are keyed by the composed label. `evaluation/circuits.py` names composed circuits
`<base>__<granularity>`, and their counts are `count_masks` dicts, which the writer reads as
`active`.

## TDD evidence

| slice | RED | GREEN |
| --- | --- | --- |
| first verdict (a) at the write seam | `ImportError: cannot import name 'format_control_summary'` | `1 passed` |
| 27 further tests (b, c by KL, c by distinct-2, null, honest-row sign and order, 80 percent boundary pure and through the suite, missing rule cell, missing delta, empty dir, gate with missing inputs, n/a variants, FAR/SDR pairing, conditions, caveats, NLS retune, overlap and deltas, coarse mapping, coarse missing, eval 5 presence, eval 5 ref-NLL, eval 5 distinct-2, CLI) | 3 failed: row order (sorted, not rule order), a wrong float precondition in my boundary test, CLI file absent | `28 passed` |

The other 24 of those 27 tests passed on first run. The library was written as one block after the
first RED, so that is horizontal slicing, and I am reporting it plainly. The boundary test was then
checked to be load-bearing: with `TOL = 0` the exact-80 percent case returns (b). The `{active,
total}` counts handling was fixed before its assertion was added, so that assertion was never seen
RED.

## Tests (full suite, both envs)

| env | result | failures vs baseline |
| --- | --- | --- |
| login base (py3.9, transformers 4.57.3) | 8 failed, 727 passed, 20 skipped | exactly the 8 baseline names |
| mgnp (py3.12, transformers 5.13) | 8 failed, 728 passed, 19 skipped | exactly the 8 baseline names |

These runs had 28 summary tests. A 29th test, pinning "fail plus missing gives (b)", and a wording
change in `DECISIONS_TAKEN` came after them. The summary test file alone was rerun: 29 passed in
both envs. Commands were run from the worktree root with BLAS threads pinned:
`<python> -m pytest tests/ -q -p no:cacheprovider`. No `core.*` dumps were left.

## Smoke check on real JSON

Real cells from the 2026-09-22 rerun were symlinked into a stand-in D/H/F suite in job tmp: far x
far, ser x far and sdr x far. Two real eval 5 `benchmarks.json` files were added the same way. The
CLI ran and parsed every field: variant rows, the null stats, wikitext, generation examples, and
the eval 5 configs, nulls and coherence. It reproduced the real FAR D numbers and listed the 30
absent cells and inputs as missing. The verdict there means nothing, because those circuits are not
D/H/F.

## Follow-up after 837e6b3: reading cells by the manifest index (ticket 04, 4e12a1d)

Ticket 04's `suite_manifest.json` now has a per-suite `cells` index. Each entry gives the circuit,
the dataset, the condition, the roles, the job, and the path under the suite root.

**Changes:**
- `summarize` / `write_summary` take `manifest=`. When the manifest indexes the suite, each cell is read from its indexed `path`.
- The dataset condition is taken from the index; the source order is manifest, then suite.json, then the condition the role implies. The header and `decision.json` record that source.
- The condition drives the label convention of the variant rows. A dataset whose condition differs from its role's expected one is listed in the missing section.
- Indexed cells outside the writer's grid are reported missing when absent.
- A manifest that lacks the suite falls back to the default layout and says so.
- The CLI gains `--manifest`, defaulting to `outputs/_launch_format_control/suite_manifest.json` when it exists. Pass `''` to turn it off.
- `expected_cells(family, task)` exposes the writer's grid. A contract test asserts it equals the real manifest index for all three suites, and it passes on the committed manifest.

**TDD:**
- RED: 4 failed. They were the manifest-path, condition, out-of-grid and fallback tests; `summarize` had no `manifest` argument. GREEN: 33 passed.
- RED: 2 failed. `expected_cells` did not exist, and the CLI rejected `--manifest`. GREEN: 34 passed in both envs.

**Full suite after the follow-up:**

| env | result | failures vs baseline |
| --- | --- | --- |
| login base | 9 failed, 769 passed, 20 skipped | the 8 baseline names, plus 1 in a file I did not write |
| mgnp | 9 failed, 770 passed, 19 skipped | the 8 baseline names, plus 1 in a file I did not write |

The extra failure is in ticket 06's in-progress file, and it fails identically in both envs. The
assertion expects the text `ARGV --circuit D=` but gets `command: python .../fake_evaluate.py
--circuit D=...`. None of my files are involved.

```
tests/test_format_control_eval5.py::test_dry_prints_the_command_runs_the_dry_run_and_the_submit_line
```

## How to run on a real suite (after `postprocess.sh <suite>`)

```
cd Deception-Circuit/.claude/worktrees/format-control
python write_format_control_summary.py outputs/_suites/format-control-far-nls0.3
python write_format_control_summary.py outputs/_suites/format-control-sdr-nls0.3
python write_format_control_summary.py outputs/_suites/format-control-sdr-coarse-nls0.3
# after ticket 06's eval 5 suites exist:
python write_format_control_summary.py outputs/_suites/format-control-far-nls0.3 --eval5-dir <sm dir> --eval5-dir <lb dir>
```

## Self-review

- **Spec axis.** Every ticket bullet except the real-suite run is covered and tested.
- **Orchestrator rulings encoded:**
  - pairing is read from `source_counts`, with the honest-split share printed;
  - the H column is always unpaired;
  - F-data variant cells read "n/a (condition is nopressure)";
  - coarse cells are reported heads-only at head level;
  - the margin, the F NLS and the eval 5 caveats are emitted;
  - the rule is stated as evaluated on eval 2 alone until `--eval5-dir` is given.
- **Standards axis.** The code uses CONTEXT.md vocabulary: Format Circuit, nopressure, Honest Twin and Pressure Clause. "control" is never used for F. There are no new dependencies, and the code is py3.9-compatible.
- **Known limitations:**
  - The eval 5 role mapping assumes ticket 06 labels circuits `D`, `H`, `F`, optionally with `_hko` or `__leaf` / `__head` suffixes. Other labels will show up as "eval 5 cells of X" missing.
  - Eval 5 aggregates average over whatever datasets each circuit has. If D and F have different dataset sets, the means are over different sets.

## Concerns

1. `postprocess.sh` belongs to ticket 04 and still calls the placeholder writer. I sent the
   orchestrator the exact two-line replacement and did not edit the file.
2. The 0.5 distinct-2 threshold and the (c)-first order are my choices, not pre-registered numbers.
   The researcher should confirm them before the real verdicts are read.
3. On the real FAR cell, D's knockout raises the deceptive answer under no_pressure from 0.058 to
   0.934, an honest-answer drop of 0.876. The honest-answer rows on D data are therefore dominated
   by the interchange source. The spec's Further Notes say as much, and it may decide condition 2
   for every task.
4. Not run: the code-review skill and the independent review. The orchestrator reviews.

## Fix round 1 (review of 14b5689, three Important findings)

The review is `reports/05-summary-writer-and-decision-rule-review.md`. All three fixes were written
test first.

**1. The training-share caveat used all splits pooled.**
- `pairing_info` now records each split's own `honest_share` and a `train_honest_share`. It no longer computes a pooled share.
- The caveat reads "F trained on N% honest-split instances (train h/n)", followed by the validation and test shares listed separately.
- On SDR counts it prints 29% (44/150), not 12%. The FAR caveat now reads: train 99% (149/150), validation 100% (150/150), test 98% (492/500).
- Covering tests: `test_paired_sdr_format_data_is_flagged_from_source_counts` expects 29% and asserts that no caveat says 12%. `test_unpaired_far_format_data_is_flagged_from_source_counts` checks the FAR text.

**2. An unassessed (c) gate counted as a pass.**
- `decide` now records `gate.assessed`. If the gate does not fire and either input is unknown, the verdict is undecided, even when a condition fails. (c) pre-empts both (a) and (b).
- A missing F distinct-2 is now listed under the missing inputs, as "F distinct-2 (source)", next to "F wikitext KL".
- Covering tests:
  - `test_unassessed_kl_gate_leaves_the_verdict_undecided` uses eval 5 with F's KL missing; it previously gave (a).
  - `test_unassessed_distinct2_leaves_the_verdict_undecided` uses no eval 2 generations; it previously gave (a).
  - `test_unassessed_gate_is_undecided_even_when_a_condition_fails` checks that the verdict is not (b).
  - The existing `test_kl_gate_still_decides_c_when_other_inputs_are_missing` still gives (c).

**3. The honest-answer rows (ruling: spec rows only by default).**
- `decide`, `summarize`, `write_summary` and the CLI take `honest_rows`, with the CLI flag `--honest-rows {variants,all}`. The default is `variants`.
- In `variants` mode the rule rows are honest_instruction and no_pressure on D data. The H and F test-set drops move to `informational_rows` and are still shown.
  - In the decision table they are labelled "informational: not in the rule".
  - The F test set row instead reads "informational: in-distribution for F; not in the rule".
  - An automatic caveat says the same.
- In `all` mode the test-set rows join the rule, and the caveat warns that this tilts the rule toward (b).
- The mode and the text "orchestrator ruling 2026-10-13: spec rows only; researcher may flip" are printed in the summary. They are also recorded in `decision.json` (`honest_rows_mode`, `honest_rows_ruling`) and in `decisions_taken`.
- Covering tests:
  - `test_honest_rows_modes_disagree_when_only_a_test_set_row_fails`: F is worse only on the H test set. `variants` gives (a) and `all` gives (b), with both modes' rows and labels asserted.
  - `test_honest_rows_mode_is_rejected_when_unknown` checks that an unknown mode raises.
  - The CLI test passes `--honest-rows all`.
- Existing tests that relied on the H-data cell being a rule input now run under `all`. They are the missing-cell test, the failed-plus-missing test and the gate-with-missing test. A new `test_missing_d_data_knockout_leaves_the_verdict_undecided` covers the default mode.

**RED, then GREEN:**
- RED: 12 failed, 28 passed. The failures were the 3 findings' new tests and the existing tests updated for the new behaviour.
- A first GREEN attempt failed: inside `summarize`, the per-side drops dict was also named `honest_rows` and shadowed the mode, so the check raised `ValueError`. Renaming the dict fixed it.
- Then 1 failure remained, a capitalisation mismatch in the mode line, which was reworded.
- GREEN: 40 passed.

Command, run in each env with BLAS threads pinned:

```
<python> -m pytest tests/test_format_control_summary.py -q -p no:cacheprovider
```

| env | result |
| --- | --- |
| login base | 40 passed |
| mgnp | 40 passed |

The real-JSON stand-in suite was re-run after the fixes. It printed the mode line, the informational rows and the labelled gate line, and the gate read real generation data: distinct-2 0.932, assessed.

Not addressed, since they were not in this round: the review's Minor items 1 to 4.
- Eval 5 role collisions overwrite silently.
- A non-positive D drop passes condition 1 trivially.
- A dead `task.full` fallback remains.
- Eval 5 means are not restricted to shared datasets. `DECISIONS_TAKEN["collateral"]` claims that restriction, so the text and the code disagree until Minor 4 is fixed.

## Fix round 2 (Minor 4, and merging the two eval 5 groups)

Ticket 06's implementer checked that the existing `load_eval5` reads its suite layout, so the
reader needed no interface change. The layout is `cells/<label>/<task>/<ablation>/benchmarks.json`,
with roles D/H/F (fine) or `X_hko__leaf` (coarse). The writer is invoked with both groups:
`--eval5-dir outputs/eval5_format_<family>` and `--eval5-dir outputs/eval5_format_<family>_lb`.

**Minor 4: the eval 5 collateral now compares only datasets both D and F have.**
- In `summarize`, the shared set is the intersection of D's and F's eval 5 datasets, with the sm and lb groups already merged by `load_eval5`. The ref-NLL rise of each circuit is the mean over that shared set.
- A dataset only one circuit has is excluded. It is recorded as `conditions[collateral].datasets` and `.excluded` in `decision.json`, and named in the summary on one line: "Eval 5 collateral compares the N benchmark dataset(s) both D and F have (...); excluded from the comparison (not shared by D and F): ...".
- With no shared dataset, the collateral input is missing and the verdict is undecided.
- The (c) gate's distinct-2 still uses all of F's datasets, because it compares F against its own full model.
- The `collateral` and `distinct2` texts in `DECISIONS_TAKEN` now state exactly this. Text and code agree.

**Two `--eval5-dir` values.** `load_eval5` already merged directories. A test now pins that merge.

**Covering tests:**
- `test_eval5_collateral_compares_only_datasets_both_circuits_have`. D has an extra lb dataset with a ref-NLL rise of 4.7. Pooled, D's mean is 2.37 and F's 1.4 passes, giving (a). Over the shared datasets D's mean is 1.2, so F fails and the verdict is (b). The test also asserts the excluded list and the summary line.
- `test_eval5_without_shared_datasets_leaves_collateral_missing` checks that the verdict is undecided and that the reference-NLL rise is listed as a missing input.
- `test_two_eval5_groups_are_merged`. The sm and lb suites are passed as two directories. All four datasets appear in the table, the collateral means cover all four, and `eval5_dirs` lists both.
- `make_eval5` gained per-role dataset lists, per-dataset ref-NLL values and a directory name.

**RED, then GREEN:**
- RED: 3 failed, 40 passed. The failures were `2.3666 != 1.2` (the pooled mean), an (a) where undecided was expected, and `KeyError: 'datasets'`.
- GREEN: 43 passed.

Command, run in each env with BLAS threads pinned:

```
<python> -m pytest tests/test_format_control_summary.py -q -p no:cacheprovider
```

| env | result |
| --- | --- |
| login base | 43 passed |
| mgnp | 43 passed |

The review's Minor items 1 to 3 remain open: eval 5 role collisions overwrite silently, a non-positive D drop passes condition 1 trivially, and a dead `task.full` fallback remains.

## SDR real-suite round (2026-10-15)

The orchestrator asked for four caveats the data supports, plus a statement of what the null samples. None of them changes the rule. All were written test first.

**What changed in `evaluation/format_control_summary.py`:**
1. **Saturation.** `diagnose()` flags saturation when D's and F's knockout accuracies on D data are both below `SATURATION_ACC = 0.02`. The caveat then reads: "atomic knockouts saturate; the deception-drop condition is trivially satisfied; eval 5 is the discriminating comparison", followed by both accuracies.
2. **Non-discriminating honest rows.** For each rule row, `diagnose()` computes the binomial standard error of the difference of D's and F's knockout accuracies, sqrt(pD(1-pD)/n + pF(1-pF)/n), with n read from the variant row's knockout `n`. A row is flagged when |F - D| < SE and the spread of D, H and F is also < SE. The caveat reads "variant rows read the ablation source; condition non-discriminating at n=…", followed by each flagged row's numbers. `knockout_row` and `variant_row` now carry `n`.
3. **(c) with D also failing the gate.** `decide()` records `gate.d_kl` and `gate.d_fails_kl_gate`. When the verdict is (c) and D's own wikitext KL is also above 0.66, the sentence becomes `both_fail_sentence()`.
   - It says "both D and F knockouts fail the gate at this NLS; the comparison is incoherent on both sides; researcher decides".
   - It lists D's, H's and F's KL, and notes that a lower NLS gives a larger circuit, so the spec's literal remedy would make F's knockout more destructive. It ends "Nothing is launched".
   - `decision.json` keeps the spec's sentence as `spec_sentence`. H's KL now reaches `decide()` through `inputs["H"]`.
4. **Retune outcome.** `retune_caveat()` reads F's `size_check.json` (ticket 03, e2a1b2b) and uses `gaps`, `retune.nls`, `retune.in_run_gate.passes`, `kl_div`, `misses`, `retune.gaps` and `carried`. For FAR it reads: "F oversized at NLS 0.3 (+71% heads, +139% fine units); retune to 0.4 failed the in-run gate (KL 0.214, misses kl_div; still +50% heads, +97% fine units); carried nls0.3." A `within_tolerance` verdict gives no caveat, so the SDR runs get none.
5. **Null sampling.** `null_sampling_of()` reads the knockout cells' counts, `geometry.head_dim` and `cli.null_alloc` / `knockout_null_count` / `knockout_granularity` from `suite.json`. It prints one line under the paired-table header and records it in `decision.json` as `null_sampling`.
   - Coarse heads-only cells have `attention_neurons = heads x 128` and no MLP units, which the real coarse suite confirms for every `_hko__leaf` cell. The null therefore samples **whole heads**, with layer-matched head counts and no MLP units.
   - Fine cells sample fine units: layer-matched heads, neurons placed inside the drawn heads with `uniform` allocation, and layer-matched MLP units.
   - The source is `evaluation/masks.py` `sample_random_masks`.

A small wording change: D's margin now reads "not recorded in its config.json" instead of "-". The 2026-08 D runs predate `--deception-margin-loss` in their configs.

**Tests (9 new or rewritten):**
- **Saturation:** `test_saturated_knockouts_on_d_data_are_caveated` and `test_unsaturated_knockouts_are_not_caveated`.
- **Honest rows:**
  - `test_rule_rows_within_binomial_error_are_caveated_non_discriminating` uses the real coarse SDR numbers. The honest_instruction row is flagged with SE 0.0191. The no_pressure row is not flagged, since 0.026 > 0.0187.
  - `test_separated_rule_rows_are_not_caveated` covers the negative case.
- **Gate:**
  - The old (c) test (D 0.80, F 0.70) is now `test_verdict_c_with_d_also_failing_the_gate_replaces_the_remedy`.
  - `test_format_knockout_above_the_kl_gate_is_verdict_c_with_the_spec_remedy` uses D 0.50 and F 0.70.
- **Retune:** `test_failed_retune_is_caveated_from_size_check` uses the real FAR `size_check.json` shape. `test_size_within_tolerance_has_no_retune_caveat` covers the negative case.
- **Null:** `test_null_sampling_is_stated_for_fine_cells` and `test_null_sampling_is_whole_heads_for_heads_only_cells`.
- **Fixture:** variant `n`; real-shaped circuit counts, geometry and `cli` in `suite.json`; coarse `X_hko__leaf` circuit entries; a `size_check=` argument.

**RED, then GREEN:**
- RED: 9 failed, 43 passed.
- GREEN: 52 passed in both envs.

```
<python> -m pytest tests/test_format_control_summary.py -q -p no:cacheprovider
```

| env | result |
| --- | --- |
| login base | 52 passed |
| mgnp | 52 passed |

**Real suites, regenerated with `python write_format_control_summary.py outputs/_suites/<suite> --data-dir data/datasets`:**
- `format-control-sdr-nls0.3` is **(c)**, with the both-fail sentence. Wikitext KL is D 1.383, H 0.694, F 1.342. Caveats: saturation, and both honest rows non-discriminating (D and F are identical at 0.522 and 0.535).
- `format-control-sdr-coarse-nls0.3` is **(a)**. Caveats: saturation (D 0.002, F 0.000). Only the honest_instruction row is non-discriminating (|F - D| 0.011 < SE 0.019). The null samples whole heads.
- Neither suite lists anything missing. The paired numbers are quoted in the ticket Comments.

**Discrepancy with the request.** The orchestrator expected both coarse rows to be non-discriminating. Under the specified criterion only honest_instruction is. On no_pressure, D and F differ by 0.025 (0.026 before rounding) against an SE of about 0.019. A one-proportion SE at p = 0.5 would be 0.016 and would not flag it either. Flagging that row would need a looser criterion, for example 2 SE.

The orchestrator ruled on 2026-10-15 to keep the 1 SE criterion as implemented.

## FAR round (2026-10-15): two additions, all three suites regenerated

Both additions were written test first; the rule is unchanged.

**What changed in `evaluation/format_control_summary.py`:**
1. **(c) with an oversized F.** `f_size_inputs()` reads F's `size_check.json`: `gaps.heads`, `tol`, `retune.nls`, `retune.in_run_gate.passes` and `kl_div`. It also reads the retuned F's side-job knockout KL from `<suite>/_side_F<NLS x 10>/cells/*/*/*/knockout.json`, which is `_side_F04` for FAR.
   - `decide()` records `gate.f_oversized` and `gate.side_kl`. When the verdict is (c) and `gaps.heads > tol`, `oversized_clause()` replaces the remedy: "F is already oversized (+71% heads); the spec's remedy (lower NLS) enlarges it further (higher NLS = smaller circuit); the one allowed retune toward smaller (NLS 0.4) also failed the in-run gate (KL 0.214) and its side-job knockout KL is 2.317; researcher decides."
   - The side-job clause is omitted when no side cell exists. `spec_sentence` keeps the spec text.
   - If D's knockout also fails the gate, the D-also-fails sentence comes first and the oversized clause is appended.
2. **Every circuit's KL on the gate line.** `decide()` records `gate.h_kl` beside `gate.d_kl`. When the verdict is (c), the gate line adds "Wikitext KL/token of every knockout: D x (passes|FAILS), H y (...), F z (...) (gate 0.66)".
3. **Delta table, checked without a code change.** FAR's `flip_audit.json` marks the leaf cells D-F, D-H-F and F-D-H as "positional default". The flip-audit column shows each on its leaf row, with the head rows marked "(primary)". A test now pins this.

**Tests (5 new):**
- `test_verdict_c_with_an_oversized_format_circuit_replaces_the_remedy` uses the real FAR `size_check.json` shape and a side cell at KL 2.317.
- `test_oversized_remedy_omits_the_side_job_clause_without_its_cell`.
- `test_size_within_tolerance_keeps_the_spec_remedy`.
- `test_gate_line_prints_every_circuits_kl_when_c_fires` checks that the line appears under (c) and not under (a).
- `test_leaf_positional_defaults_show_beside_primary_head_rows`.
- The fixture gained `side_kl=`.

**RED, then GREEN:**
- RED: 3 failed, 54 passed. The within-tolerance test and the leaf-positional test passed on first run; they pin behaviour the writer already had.
- One more failure was a capitalisation mismatch in my own test's expectation, since the clause starts a sentence.
- GREEN: 57 passed.

```
<python> -m pytest tests/test_format_control_summary.py -q -p no:cacheprovider
```

| env | result |
| --- | --- |
| login base | 57 passed |
| mgnp | 57 passed |

**All three suites were regenerated with the CLI; no cell was re-run.**

| suite | verdict | KL D / H / F | missing |
| --- | --- | --- | --- |
| `format-control-far-nls0.3` | (c), oversized-F sentence | 0.327 / 2.784 / 4.265 | none |
| `format-control-sdr-nls0.3` | (c), D-also-fails sentence | 1.383 / 0.694 / 1.342 | none |
| `format-control-sdr-coarse-nls0.3` | (a) | 0.364 / 0.275 / 0.279 | none |

The paired numbers and caveats are quoted in the ticket Comments. The ticket is set to resolved; the review box is the orchestrator's.

**A FAR observation for the researcher.** Under ticket 01's fixed prompt derivation, FAR's full model still answers deceptively on the D-data variant rows: 0.839 with the honest instruction and 0.871 with no pressure. Every knockout lowers that to between 0.08 and 0.17. The rule's honest-answer drops there are therefore negative, meaning the knockouts make the model more honest. Before the fix, the 2026-09-22 rerun had the full model at 0.106 and 0.058 on those rows.

## Whole-branch review fix wave (I1, M5)

The review is `reports/07-whole-branch-review.md`. Both fixes were written test first. By ruling, the verdict logic is unchanged.

**I1: eval 5 and the eval 2 conditions.**
- **(a) The choice is recorded.** `DECISIONS_TAKEN["eval2_conditions"]` states that the deception-drop and outside-null conditions are evaluated on eval 2 (task accuracy and its task-side null) even when `--eval5-dir` is given. Eval 5 enters the rule only through collateral (the reference-NLL rise) and the distinct-2 gate. The entry is labelled "not pre-registered; orchestrator choice 2026-10-15, researcher to confirm". It is written to `decision.json` `decisions_taken` and to the summary's "Decisions taken" list.
- **(b) The saturation caveat is reworded.** It now reads: "atomic knockouts saturate, so the eval 2 deception-drop condition is trivially satisfied and cannot tell D from F; the rule still evaluates it on eval 2 (eval 5's deception drop, when given, is informational and not in the rule)". It no longer says "eval 5 is the discriminating comparison".
- **(c) An informational eval 5 row.** `eval5_aggregate()` now also returns `deception_drop`, the mean over datasets of the full-model deception rate minus the knockout deception rate, both under interchange.
  - With `--eval5-dir`, `summarize()` computes it for D and F over the datasets they share. It records it as `decision.json` `eval5_deception_drop`, with `datasets` and `in_rule: false`.
  - The decision table prints it directly under the rule's deception-drop row, as "deception drop, eval 5 (informational: not in the rule)". Its result column is "-".
  - Without `--eval5-dir` the field is null and no row is printed.

**M5: the CLI docstring.** The `--eval5-dir` example now uses `outputs/eval5_format_far` and `outputs/eval5_format_far_lb`, the names in ticket 06's `README_eval5.md`. It also names the SDR and SDR-coarse equivalents. Those directories do not exist yet, because eval 5 has not been launched.

**Tests (3 new, 1 updated):**
- `test_eval2_reading_of_deception_drop_and_nulls_is_recorded_as_a_choice`.
- `test_eval5_deception_drop_is_an_informational_row_beside_the_rules_row`. The eval 5 drops are D 0.900 and F 0.600, so F < 0.8 x D on eval 5, yet the verdict stays the eval 2 rule's (a). The test also checks that the row sits directly under the rule's row.
- `test_no_eval5_deception_row_without_an_eval5_directory`.
- `test_saturated_knockouts_on_d_data_are_caveated` now expects the new wording and the absence of the old claim.
- `make_eval5` gained `ko_rate=`.

**RED, then GREEN:**
- RED: 4 failed, 56 passed.
- GREEN: 60 passed.

```
<python> -m pytest tests/test_format_control_summary.py -q -p no:cacheprovider
```

| env | result |
| --- | --- |
| login base | 60 passed |
| mgnp | 60 passed |

**Regenerated, with no cell re-run:** FAR (c), SDR fine (c) and SDR coarse (a), unchanged, with nothing missing in any of them. The summaries contain the new decisions entry and, where the knockouts saturate, the reworded caveat. They have no eval 5 row, because no eval 5 directory exists yet.
