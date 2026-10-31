# Ticket 05 review: format-control summary writer and decision rule

Date: 2026-10-13. Reviewer: review-05 (independent, read-only), branch `format-control`.

**Head reviewed: 14b5689.** This covers 837e6b3 plus two follow-ups:
- feb168a rewords the "missing" text in `DECISIONS_TAKEN` and adds a test.
- 14b5689 reads cells through the manifest index, adds `--manifest`, `expected_cells()` and a contract test against the real index.

Files: `evaluation/format_control_summary.py`, `write_format_control_summary.py`,
`tests/test_format_control_summary.py`.

Line numbers in the Spec Compliance and Issues sections below refer to **837e6b3**. The section
"Follow-ups reviewed at 14b5689" gives the HEAD line numbers of every open finding.

When I checked, the worktree also held **uncommitted** edits on top of 14b5689. One is a new test
labelling the (c)-first order and the distinct-2 fraction as "not pre-registered". The other is an
in-progress library change to match it. That work is not reviewed here. To isolate HEAD, I extracted
14b5689 with `git archive` into job tmp and ran the tests and probes there.

## What I checked outside the diff

- **Real merged cell.** I read `cross-task-faithfulness-nls0.3-rerun260922/cells/far/far/interchange/`
  in the main checkout: `knockout.json`, `null.json`, `sanity.json`, `summary.json` and `flip_audit.json`.
  Every field the writer reads exists with the expected shape:
  - `task.knockout.accuracy` and `task.null.stats.accuracy.{p5,p50,p95}`;
  - `wikitext.discovered.kl_per_token` and `counts.ablated_fine_units`;
  - `variants.{honest_instruction,no_pressure}.rows.{full,knockout}.accuracy`;
  - `generation.examples[].continuations.{full,knockout}`;
  - `null.json anchors.full.accuracy` and `discovered.accuracy`;
  - `sanity.json rows.{full_open,discovered}.accuracy`;
  - in the flip audit, `cells[].{circuit,task,positional.verdict,headline.separable}`.
- **Producer side.** `CircuitSpec.provenance` (evaluation/circuits.py:57) writes `counts` as active
  ints for composed circuits too, so the delta "heads" column fills on real suites. The
  `overlap.py` pair schema (`pair`, `awaits`, `heads`, `fine_units`, with
  `jaccard/intersection/active_a/active_b`) matches the renderer.
- **Manifest.** `suite_manifest.json` cell labels match the writer for all three suites. Fine suites
  have `D/H/F` plus `<delta>__{head,leaf}`. The coarse suite has `X_hko__leaf` plus `<delta>_hko__leaf`.
- **Skip reason.** `ctx.variant_loader` uses `empty_variant_reason` (context.py:302), which returns
  `_nopressure_reason` (variants.py:83). That reason contains "'nopressure'", so the n/a text is
  driven by the recorded reason.
- **Label convention and headline sign.** `LABEL_CONVENTION` (variants.py:45) keeps deceptive labels on the variant rows. The evaluator's
  `headline.honest_accuracy_drop` is `full_minus_knockout` under those labels (knockout.py:235), which is
  -0.755 on the real cell. The writer computes +0.755 as the honest-answer drop and ignores the
  headline field. That is correct.
- **Eval 5.** I read a real `benchmarks.json` (`eval5_sdr_coarse_nls0.3_honest_nomb`). The fields
  `configs.{full,knockout}.rates.deceptive`, `coherence.{ref_nll,distinct_n}` and `null.deceptive.{p5,p50}`
  all match `load_eval5`.
- **Pairing data.** The real `far_nopressure` and `sdr_nopressure` `source_counts` are 8/492 and 520/0, as the constraint states.
- **Tests.** I ran the focused file in the base env on the current worktree: 34 passed. That is the committed 28 plus the uncommitted 6.

## Spec Compliance

- ✅ **0.8 boundary is `>=`** with a 1e-9 tolerance (format_control_summary.py:415). The pure test and the through-the-suite test both pin it, and the implementer showed the tolerance is load-bearing.
- ✅ **Null direction.** Outside means knockout accuracy strictly below the null's p5 (:332). Both D and F are required (:440-447 region, `bool(od and of)`).
- ✅ **Deception drop** is full minus knockout on D data under deceptive labels (:328-333, :548).
- ✅ **Honest-answer drop sign.** D-data variant rows use knockout minus full under deceptive labels. H and F test sets use full minus knockout under honest labels (:367, :552-553). The real-cell value 0.755 is reproduced in a test.
- ✅ **Collateral** is the wikitext KL of eval 2, switching to the mean ref-NLL rise only with `--eval5-dir`. The summary states "evaluated on eval 2 alone until an eval 5 directory is given".
- ✅ **(c) gate.** KL/token above 0.66 fails, and 0.66 itself passes. Distinct-2 collapse is also checked. The (c) sentence includes "retrain the Format Circuit at a lower NLS".
- ✅ **Paired table.** It has one sub-table per dataset column and one row per circuit, with circuit-alone, intact, knockout, drop, null p5/p50/p95, outside-null, wikitext KL, flip audit and the paired flag.
- ✅ **Pairing from data.** F is paired iff the test split has `honest_split == 0` (:205-218). The H column is always unpaired. The share is printed.
- ✅ **Variant n/a.** F-data variant cells read "n/a (condition is nopressure)" from the recorded `skipped` reason (:353-358), never "missing". The test asserts on the rendered markdown.
- ✅ **Overlap and delta rows.** Overlap shows D/H, D/F and H/F. Delta rows show head primary for fine suites, and "head (composed at leaf)" with heads-only knockouts for coarse ones. Each delta row carries size, knockout accuracy, null and the positional-default verdict.
- ✅ **Missing cells** go to a "Missing" section with no crash, including an empty suite directory.
- ✅ **Eval 5 columns** appear only when a directory is given. The test asserts this on both the markdown and the JSON.
- ✅ **decision.json** carries each sub-condition's pass/fail, the verdict, the spec sentence, thresholds, the rule order and the decisions taken.
- ❌ **"F trained on N% honest-split instances" reports the wrong share** (:604 using :218). See Important 1.
- ❌ **(a) can be issued while the (c) gate is unassessed** (:402-407, :456-462). See Important 2.
- ⚠️ **Honest-answer rows need a ruling** before real verdicts are read: the rule uses all four rows, F <= D on every one. See Important 3.
- ⚠️ **Researcher sign-off needed on two of the implementer's own choices.** They are disclosed, recorded in `decision.json` and not pre-registered. They do not block this ticket.
  - The (c) gate is checked before (a) (:87). The spec's literal wording lets (c) override only (b).
  - The 0.5 distinct-2 collapse fraction (:66), with eval 2's proxy of word bigrams over three 48-token continuations (:280).

## Strengths

- **Stdlib only.** The library imports no torch, which keeps the writer cheap and testable in both envs. It reimplements `condition_of` and the label convention in a few lines with comments pointing at the originals.
- **Tests assert at the seam.** Almost every test reads the written `evaluation_summary.md` or `decision.json`. Only the two boundary tests call the pure `decide`, which is appropriate for a boundary.
- **Fixture numbers trace to real data.** The D-data honest-instruction row is the real FAR cell, so the sign convention is checked against data rather than against the implementer's belief.
- **The writer avoids the evaluator's mis-signed headline field.** It ignores `headline.honest_accuracy_drop` and explains why.
- **Decisions and inputs are visible.** Every rule input is written to `decision.json`, and the implementer's decisions are listed there for the researcher.

## Issues

### Critical

None.

### Important

1. **The training-share caveat uses all splits, not the training split.**
   - **Where:** evaluation/format_control_summary.py:218 and :604, locked in by tests/test_format_control_summary.py:395.
   - **What:** `honest_share` is `honest_split / total` summed over train, validation and test. The caveat says "F trained on N% honest-split instances". On the real SDR data it prints 12%. The training split is actually 44/150, or 29%, and train plus validation is 33%. FAR prints 99% either way, which hides the bug.
   - **Why:** a researcher reads this caveat as a statement about how contaminated F's training set is. Including the 520 deceptive-split test instances understates the SDR share by more than half.
   - **Fix:** compute the share from `splits["train"]`, or from train plus validation if that is what "trained on" should mean. Say which in the caveat, and update the test to expect 29% for SDR.

2. **(a) or (b) can be issued while the (c) gate cannot be assessed.**
   - **Where:** evaluation/format_control_summary.py:402-407 and :456-462.
   - **What:** `gate["fails"] = bool(kl_fails or degenerate)` treats an unknown input as a pass. I probed the committed `decide` directly:
     - With eval 5 and F's wikitext KL missing, the verdict is (a). "F wikitext KL" appears in `missing`.
     - With eval 2 and F's distinct-2 missing, the verdict is (a), and nothing appears in `missing`.
     - With F's KL missing and the deception condition failing, the verdict is (b).
   - **Why:** the spec makes incoherence override every verdict, so (a) and (b) are both meaningful only once the gate is known. The `DECISIONS_TAKEN["missing"]` text promises an undecided verdict when inputs are missing, but the code applies that only to the four conditions. This bites only on a cell run with `--skip-wikitext` or `--gen-examples 0`, or one with missing generation examples. When it does, the headline verdict is wrong.
   - **Fix:** when the gate has not fired and either `kl_fails` or `degenerate` is None, return verdict None. Add "F distinct-2" to `missing` symmetrically with "F wikitext KL". Add a fixture test for each case.

3. **The four-row honest-answer condition is structurally tilted toward (b).**
   - **Where:** evaluation/format_control_summary.py:425-433 and :552-553, with the decision at :89. The fixture defaults sit at tests/test_format_control_summary.py:87-89.
   - **What:** condition 2 requires F <= D on every row, including the F test set. On that row F's knockout is evaluated on its own training distribution, which F was pruned to be faithful on. D's knockout on the same row is out of distribution. F's in-distribution knockout will almost always drop honest accuracy more, so condition 2 fails and the verdict is (b) whatever the deception numbers say. (b) is the outcome the researcher hopes for, and (a) is the outcome the study guards against. The fixture hides this, because its defaults give F's knockout on F data a smaller drop than D's (0.26 against 0.36), which is the unlikely case.
   - **Why:** the spec's headline metric (i) names only "the honest-answer drop on the no-pressure and honest-instruction rows of eval 2". The ticket's facts add the H and F test sets to the definition of honest-answer drop, but neither text says every row must pass. This is not a coding error, since the implementer disclosed the choice. It does decide the pre-registered verdict, so it needs a ruling before any real verdict is read.
   - **Fix:** have the researcher rule on one of two options:
     - Restrict condition 2 to the eval 2 variant rows, as the spec's (i) does, and show the H and F test-set rows as context only.
     - Keep all four rows but state the asymmetry in a caveat.

     Either way, add a fixture in which F's knockout on F data is the larger drop, so the rendered verdict for that case is pinned.

### Minor

1. **Eval 5 role collisions overwrite silently** (:222-239). `_role_of` maps both `D` and `D_hko__leaf` to D, and the `<ablation>` glob is `*`. Two cells of one role, or two ablations, therefore overwrite each other per dataset name with no notice. Sorted order happens to let `_hko__leaf` win. Fix: prefer the `_hko__leaf` cell explicitly for coarse suites, filter to `interchange`, and list collisions under Missing.
2. **A non-positive D deception drop passes condition 1 trivially** (:415). If D's knockout does not reduce deception, `F >= 0.8 x D` passes for almost any F. The null condition usually catches this case. A one-line caveat or a `dd > 0` requirement would make it explicit.
3. **One full-accuracy fallback is dead code** (`_full_accuracy`, around :296). It reads `knockout.json task.full.accuracy`, but real knockout files have only `task.circuit` and `task.knockout`. The fallback is harmless and could be removed, or replaced with the variant rows' `full`.
4. **Eval 5 means can cover different dataset sets.** The implementer noted this. If D and F cover different datasets, the mean ref-NLL rises are not comparable. Restrict the comparison to the shared datasets, as `DECISIONS_TAKEN["collateral"]` already claims ("over the benchmark datasets both circuits have"). The code does not do this yet.

## Follow-ups reviewed at 14b5689

**feb168a: the "missing" wording.** The new text says the verdict is undecided "unless the (c) gate
fires or another condition already fails, which rules (a) out and gives (b)" (:100-102). This now
matches the code, and the new test `test_failed_condition_decides_b_even_when_another_input_is_missing`
pins it on the written decision.json. The test and the wording are correct for missing **condition**
inputs.

It does not close Important 2. The wording lets a failed condition give (b) even when F's wikitext
KL or distinct-2 is missing. In that case (c) could not be assessed, and (c) overrides (b). I re-ran
the probes against the HEAD file, with the same results as at 837e6b3:

| case | verdict at HEAD | listed missing |
| --- | --- | --- |
| eval 5, F wikitext KL missing | (a) | F wikitext KL |
| eval 2, F distinct-2 missing | (a) | nothing |
| F KL missing and the deception condition fails | (b) | F wikitext KL |

**14b5689: manifest index.**
- ✅ When the manifest indexes the suite, cell paths come from each entry's `path`. Otherwise the reader falls back to the default layout and notes the fallback (:160-174, :176-188).
- ✅ Dataset conditions come from the manifest, then from suite.json's task provenance, then from the role (:506-523). `variant_row` now takes the dataset's condition, so the sign convention follows the data rather than the column name.
- ✅ Indexed cells outside the writer's grid are still reported missing (:597-601).
- ✅ `expected_cells` (:149) is pinned against the real launcher manifest by `test_the_writers_grid_is_exactly_the_launchers_cell_index`. It ran at HEAD and was not skipped, so all three real suites' cell sets equal the writer's grid.
- ✅ The CLI's default manifest path is relative to the repo root. `postprocess.sh` runs `cd "$(dirname "$0")/../.."` before calling the writer, so the default resolves there. Elsewhere it falls back silently to the default layout, and `decision.json` records `manifest_indexed: false`.
- **Tests:** HEAD's test file against HEAD's library, extracted to tmp, gives 34 passed and 0 skipped.

**New Minor items from the follow-ups:**
5. **A condition mismatch is listed under "missing"** (:546-549). A dataset whose recorded condition differs from the expected one is a contradiction, not a missing input. Give it its own "inconsistent" line, or make it a caveat.
6. **The manifest is parsed twice** (:539). `load_manifest_index` already loaded it. Return the suite entry from that function instead.

**Open findings at HEAD (line numbers at 14b5689):**
- **Important 1:** `honest_share` is still computed over all splits (:252) and used by the caveat (:683). The test still asserts 12% for SDR (tests :405).
- **Important 2:** an unknown gate input still counts as a pass (:436-440, :490-496).
- **Important 3:** the every-row honest-answer condition still includes the F test-set row (:459, :631).

## Assessment

**Needs fixes, at HEAD 14b5689.** The two follow-ups are sound and well tested. Neither one touches Important 1, 2 or 3. The rule's arithmetic is correct, and so are its direction conventions: the 0.8 boundary, the null direction, the sign under deceptive labels and the KL gate. Every field read was confirmed against real cells and ticket 04's producers. Tests assert on the produced markdown and JSON. Two defects must be fixed before the real verdicts are produced: the "F trained on" share is wrong (Important 1), and the gate can be unassessed under an (a) or (b) verdict (Important 2). Important 3 needs a researcher ruling on the honest-answer rows before any real verdict is read.

## Re-review of fix round 1 (f8bd30b..f20341a)

Read from the fix diff and the implementer report only. No test run (no specific doubt). The report names covering tests and shows RED (12 failed) then GREEN (40 passed in both envs).

### Finding Verdicts

1. **ADDRESSED.** `pairing_info` now stores per-split `honest_share` and `train_honest_share` and no longer pools (evaluation/format_control_summary.py, pairing_info hunk at old :238-260). The caveat prints the train share, then validation and test apart. `test_paired_sdr_format_data_is_flagged_from_source_counts` now expects 29% (44/150) and asserts no caveat contains "12%". The FAR text test is updated to 99% (149/150).
2. **ADDRESSED.** `decide` adds `gate["assessed"]`, true when the gate fires or both KL and distinct-2 are known. The verdict is `None` when the gate is not assessed, checked before the (b) branch, so it also stops (b). Missing distinct-2 is now appended to `missing` as "F distinct-2 (source)". Covering tests: unassessed KL under eval 5, unassessed distinct-2, and unassessed gate with a failing condition. `test_kl_gate_still_decides_c_when_other_inputs_are_missing` still gives (c).
3. **ADDRESSED.** `decide(..., honest_rows="variants")` defaults to the eval 2 variant rows. H and F test-set rows go to `informational_rows` and are rendered with an in-distribution label for F. The mode and ruling text appear in the summary, in the caveats, in `decision.json` (`honest_rows_mode`, `honest_rows_ruling`) and in `DECISIONS_TAKEN`. The CLI has `--honest-rows {variants,all}`. `test_honest_rows_modes_disagree_when_only_a_test_set_row_fails` gives (a) under `variants` and (b) under `all` on one fixture. An invalid mode raises, and a test covers it.

### New Breakage in the Fix Diff

- No Critical or Important.
- **Minor.** `test_missing_d_data_knockout_leaves_the_verdict_undecided` skips cell F/far, which also supplies F's wikitext KL. The undecided verdict can therefore come from the unassessed gate rather than the missing deception drop. The test passes for a confounded reason. It still pins the listed "F deception drop" input.
- **Minor.** The "failed condition decides (b) with a missing input" test now runs only under `all`. No default-mode test of that path exists.
- **Minor.** `decision.json` always carries `honest_rows_ruling` text ("researcher may flip"), including in `all` mode. Harmless.

### Out-of-Scope Observations

- The earlier Minor items 1 to 4 (eval 5 role collisions, non-positive D drop, dead `task.full` fallback, collateral text claiming a shared-dataset restriction the code does not apply) were not in this round and remain open. Minor 4 leaves `DECISIONS_TAKEN["collateral"]` disagreeing with the code.

### Verdict

All three findings ADDRESSED. No blocking breakage. Round passes; the three Minors are optional.
