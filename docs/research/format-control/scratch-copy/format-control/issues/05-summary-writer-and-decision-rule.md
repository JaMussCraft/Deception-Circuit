# 05 — Suite summary writer with the pre-registered decision rule

**What to build:** A writer that reads a format-control suite directory and produces `evaluation_summary.md` plus `decision.json`: the paired table for D, H and F, the overlap table, the delta rows with their flip-audit verdicts, and the (a)/(b)/(c) verdict per task computed by the decision rule in the spec.

**Status:** resolved
**Type:** task
**Blocked by:** 04 (cell schema); can be developed against the existing `cross-task-faithfulness-nls0.3-rerun260922` cells plus a fixture

**Facts to build on**
- Spec, "Pre-registered outcomes and decision rule": F is "as effective" when its deception drop >= 0.8 × D's, its honest-answer drop <= D's, its reference-NLL rise (eval 5) or wikitext KL (eval 2) <= D's, and both knockouts are outside their own size-matched nulls (knockout accuracy below the null's 5th percentile). Else (b); (c) when F's knockout fails the wikitext KL <= 0.66 gate or its generations are degenerate (distinct-2 collapse).
- Deception drop on a task = full-model accuracy minus knockout accuracy under the deceptive-label convention (`LABEL_CONVENTION`, `evaluation/variants.py`). Honest-answer drop = the same on the `honest_instruction` and `no_pressure` variant rows and on the H and F test sets, where labels are honest (accuracy falling means honest answering is hurt).
- Existing writers to extend or mirror: `outputs/_suites/_launch_260922/write_suite_summary.py`, `write_cell_summary.py`, `outputs/llama-8b-instruct_sdr_coarse/_launch/write_evaluation_summary.py`, `evaluation/report.py`.
- Eval 5 inputs (ticket 06) arrive later: the writer takes an optional eval 5 suite directory and adds the benchmark columns (deception rate per dataset under interchange, `ref_nll`, `distinct_n`) when present; the rule is evaluated on eval 2 alone until then and says so.

- [x] `evaluation/format_control_summary.py` (library) + `write_format_control_summary.py` (CLI): reads `suite.json`, the cells and the overlap JSON; tolerates missing cells (reported in a "missing" section, never a crash).
- [x] Paired table: for each dataset column (D data, F data, H data) and each circuit row (D, H, F): intact accuracy, knockout accuracy, drop, null 5th/50th/95th percentile, wikitext KL, flip-audit verdict, paired flag (D and F columns paired by instance, H column marked unpaired); variant cells in the F-data column read "n/a (condition is nopressure)", never "missing".
- [x] Overlap table (Jaccard heads and fine units; shared head count) for D/H, D/F, H/F; delta rows for `D-F`, `D&F`, `F-D`, xor members with size, knockout accuracy, null and positional-default verdict; for fine suites both granularities with head marked primary.
- [x] Decision block: the rule's inputs, each sub-condition's pass/fail, the verdict (a)/(b)/(c), and the sentence from the spec that the verdict triggers (for (c): retrain F at a lower NLS). Written to `decision.json` too.
- [x] Caveat lines emitted automatically: variant rows at other NLS levels are suspect (ticket 01 drift fix), H column unpaired, coarse knockouts are heads-only, eval 5 absent or present.
- [x] Tests on a fixture suite directory (tiny JSON cells written by the test) covering each verdict, the 80 percent boundary, a missing cell, and the eval 5 columns appearing only when a directory is given.
- [x] Run on the three real suites from ticket 04; the three verdicts quoted in Comments with the paired numbers.
- [x] Both suites in both envs; failure names vs baseline.
- [x] Independent review (orchestrator-dispatched: build phase approved, fix round 1 re-review passed; later rounds covered by the whole-branch review); report in `reports/05-summary-writer-and-decision-rule-review.md`.

## Comments

**2026-10-13, impl-05 (build phase; the real-suite run awaits ticket 04's cells).**

Built:
- `evaluation/format_control_summary.py`: the library. It is stdlib only and does not import torch.
- `write_format_control_summary.py`: the CLI at the repo root.
- `tests/test_format_control_summary.py`: 29 tests on fixture suites the test writes, fine and coarse.

The commit was made by the orchestrator on my instruction; the SHA is in the orchestrator's log.

Usage on a real suite, from the worktree root:
`python write_format_control_summary.py outputs/_suites/format-control-far-nls0.3 [--eval5-dir DIR ...]`.

Tests:
- The new file passes 29 of 29 in both envs. The 29th test, which pins "fail plus missing gives (b)", was added after the full-suite runs.
- Full suite, login base: 8 failed, 727 passed, 20 skipped.
- Full suite, mgnp: 8 failed, 728 passed, 19 skipped.
- In both envs the failures are exactly the 8 baseline names, with no new failures.

Smoke check on real JSON: real 2026-09-22 rerun cells (far/ser/sdr on `far`) and real eval 5 `benchmarks.json` files were symlinked into a D/H/F stand-in suite in job tmp. The reader parsed every field. It reproduced the real FAR D numbers (honest_instruction honest-answer drop 0.755, wikitext KL 0.327) and listed the 30 absent cells and inputs as missing. The verdict there means nothing, because the circuits are not D/H/F.

Decisions taken in applying the rule, recorded in `decision.json` `decisions_taken` and open to the researcher:
1. The (c) gate is checked before (a).
2. F's honest-answer drop must be <= D's on every row. The rows are honest_instruction and no_pressure on D data, the H test set and the F test set.
3. On D data the variant rows keep deceptive labels, so the honest-answer drop is knockout accuracy minus full accuracy. On H and F data it is full minus knockout.
4. Distinct-2 collapse means F's knockout distinct-2 is below 0.5 of the full model's. That threshold is not pre-registered in the spec. The value comes from eval 5 `distinct_n` when given, else from word bigrams of eval 2's three wikitext continuations.
5. With eval 5, collateral is the mean reference-NLL rise (knockout minus full) over benchmark datasets. The deception drop stays eval 2's.
6. A missing rule input leaves the verdict undecided unless the (c) gate fires or another condition already fails. A failed condition rules (a) out and gives (b), with the missing input still listed.

`postprocess.sh` (ticket 04's file) still calls the placeholder writer. The exact replacement was sent to the orchestrator.

Full report: `reports/05-implementer-report.md`.

**2026-10-13, impl-05: follow-up after 837e6b3.** The writer now reads cells by ticket 04's manifest `cells` index (4e12a1d). It takes each cell's path and each dataset's condition from the index, and the CLI passes `--manifest`, defaulting to the launcher's manifest. A contract test pins the writer's grid to the real index for all three suites. The summary test file now has 34 tests, passing in both envs. The commit is requested from the orchestrator.

**2026-10-13, impl-05: rulings.** The orchestrator kept both choices. (c) is checked before (a), and distinct-2 collapse means below 0.5 x the full model's. `evaluation_summary.md` and `decision.json` now label both "not pre-registered; orchestrator choice 2026-10-13, researcher to confirm". The label appears in the rule order, the gate line, `gate.distinct2_frac_status` and `decisions_taken`. A 35th test pins it, and 35 of 35 pass in the base env. The postprocess hook-up landed in e7ebddd.

**2026-10-13, impl-05: review fix round 1 (three Important findings).**
1. The "F trained on" caveat now uses the train split's share: SDR 29% (44/150), not the pooled 12%. Validation and test shares are listed separately.
2. A missing (c) gate input (F's wikitext KL or distinct-2) now leaves the verdict undecided and is listed under missing. (c) pre-empts both (a) and (b).
3. Orchestrator ruling 2026-10-13: spec rows only; researcher may flip. The rule's honest-answer condition uses the eval 2 variant rows (no_pressure, honest_instruction) by default, set by `--honest-rows {variants,all}` with default `variants`. The H-data and F-data honest drops remain as informational rows with the caveat "in-distribution for F; not in the rule". The mode is recorded in `decision.json` and the summary.

`tests/test_format_control_summary.py` passes 40 of 40 in both envs. The fix report is in `reports/05-implementer-report.md`.

**2026-10-13, impl-05: review fix round 2 (Minor 4).** The eval 5 collateral now compares only the benchmark datasets both D and F have, with the sm and lb groups merged. Excluded datasets are named in the summary and `decision.json`. With no shared dataset the verdict is undecided. A test pins that two `--eval5-dir` values are merged. The eval 5 reader needed no interface change: ticket 06 verified it against its layout. `tests/test_format_control_summary.py` passes 43 of 43 in both envs.

- 2026-10-13 orchestrator: session stopped at its usage limit with this ticket in progress; see reports/00-orchestration-ledger.md for the exact remaining steps.

**2026-10-15, impl-05: SDR real-suite round (FAR cells still queued; that box stays open).**

The writer was re-run on both SDR suites merged in 1bc5e58, with eval 2 only and honest-answer rows `variants`. The verdicts stand mechanically; the new caveats do not change the rule.

**`format-control-sdr-nls0.3`: verdict (c).** F's knockout fails the wikitext KL gate. D's own knockout fails it too, so the remedy sentence is replaced: "both D and F knockouts fail the gate at this NLS; the comparison is incoherent on both sides; researcher decides". A lower NLS gives a larger circuit, so the spec's literal remedy would make F's knockout more destructive. Nothing is launched.

Paired numbers on D data `sdr` (n=1000, full-model accuracy 1.000):

| circuit | circuit-alone acc | knockout acc | drop | null p5 / p50 / p95 | wikitext KL |
| --- | ---: | ---: | ---: | --- | ---: |
| D | 0.950 | 0.000 | 1.000 | 0.397 / 0.705 / 0.877 | 1.383 |
| H | 0.185 | 0.000 | 1.000 | 0.297 / 0.742 / 0.933 | 0.694 |
| F | 0.244 | 0.000 | 1.000 | 0.238 / 0.740 / 0.918 | 1.342 |

- Every knockout lies outside its null, and the flip audit reads "content-driven flip; separable".
- Honest-answer drops D / H / F: honest_instruction 0.522 / 0.521 / 0.522, no_pressure 0.535 / 0.534 / 0.535.
- Overlap: D/F Jaccard 0.584 heads (52 shared; 68 vs 73 heads) and 0.311 fine units.
- The F data is instance-paired with D data: SDR's test split has 0 of 520 honest-split instances.
- Caveats: the atomic knockouts saturate, both honest rows are non-discriminating at n=1000, and F trained on 29% honest-split instances (train 44/150).

**`format-control-sdr-coarse-nls0.3`: verdict (a).** Heads-only knockouts are reported at head level, and the null samples whole heads layer by layer with no MLP units.

Paired numbers on D data `sdr` (n=1000, full-model accuracy 1.000):

| circuit | circuit-alone acc | knockout acc | drop | null p5 / p50 / p95 | wikitext KL |
| --- | ---: | ---: | ---: | --- | ---: |
| D | 0.967 | 0.002 | 0.998 | 0.041 / 0.414 / 0.774 | 0.364 |
| H | 0.682 | 0.002 | 0.998 | 0.110 / 0.525 / 0.918 | 0.275 |
| F | 0.392 | 0.000 | 1.000 | 0.041 / 0.496 / 0.747 | 0.279 |

- Every knockout lies outside its null. The flip audit separates H's knockout from its random-knockout null but not D's or F's.
- The rule's conditions all pass:
  - deception drop: F 1.000 >= 0.8 x 0.998;
  - honest-answer drop: honest_instruction F 0.519 <= D 0.530, and no_pressure F 0.535 <= D 0.560;
  - collateral: F KL 0.279 <= D KL 0.364;
  - nulls: D 0.002 < 0.041 and F 0.000 < 0.041.
- Overlap: D/F Jaccard 0.356 heads (36 shared; 69 vs 68 heads).
- Caveats:
  - The atomic knockouts saturate (D 0.002, F 0.000), so the deception-drop condition is trivially satisfied and eval 5 is the discriminating comparison.
  - The honest_instruction row is non-discriminating: |F - D| 0.011 against an SE of 0.019.
  - The no_pressure row is NOT flagged: |F - D| is 0.025 (0.026 before rounding), above its SE of 0.019. The orchestrator expected both rows to be flagged; the data does not support the second.

`tests/test_format_control_summary.py` passes 52 of 52 in both envs. The fix report is in `reports/05-implementer-report.md` under "SDR real-suite round".

**2026-10-15, orchestrator ruling (recorded by impl-05).** The 1 SE non-discriminating criterion stays exactly as implemented. Loosening it to flag the coarse no_pressure row would fit the criterion to the result, and the saturation caveat already covers the suite as a whole. The caveat round is committed. Remaining: run the writer on the FAR suite once it merges, quote its verdict with the paired numbers, and tick the last box.

**2026-10-15, impl-05: FAR round; all three real suites.**

Two additions were made test first; the rule is unchanged. First, when the verdict is (c) and F's size-check gap in heads exceeds the tolerance, the remedy sentence is replaced with the oversized-F sentence, and the spec sentence is kept as `spec_sentence`. Second, when (c) fires, the gate line prints every circuit's wikitext KL. The three suite summaries were regenerated from the merged cells (FAR 7d62b7c, SDR 1bc5e58) with eval 2 only and honest-answer rows `variants`; no cell was re-run.

| suite | verdict | why |
| --- | --- | --- |
| `format-control-far-nls0.3` | **(c)** | F's knockout fails the KL gate; F is oversized, so the remedy sentence is replaced |
| `format-control-sdr-nls0.3` | **(c)** | F's and D's knockouts both fail the KL gate; the remedy sentence is replaced |
| `format-control-sdr-coarse-nls0.3` | **(a)** | all four conditions pass, but the atomic knockouts saturate, so eval 5 must discriminate |

**FAR, verdict (c).** The sentence reads: "F is already oversized (+71% heads); the spec's remedy (lower NLS) enlarges it further (higher NLS = smaller circuit); the one allowed retune toward smaller (NLS 0.4) also failed the in-run gate (KL 0.214) and its side-job knockout KL is 2.317; researcher decides. Nothing is launched."

Wikitext KL of every knockout: D 0.327 (passes), H 2.784 (fails), F 4.265 (fails). Only D's knockout is coherent.

Paired numbers on D data `far` (n=1000, full-model accuracy 1.000):

| circuit | circuit-alone acc | knockout acc | drop | null p5 / p50 / p95 | wikitext KL |
| --- | ---: | ---: | ---: | --- | ---: |
| D | 0.969 | 0.000 | 1.000 | 0.440 / 0.872 / 0.999 | 0.327 |
| H | 0.474 | 0.000 | 1.000 | 0.297 / 0.766 / 0.949 | 2.784 |
| F | 0.733 | 0.000 | 1.000 | 0.164 / 0.638 / 0.977 | 4.265 |

- The flip audit reads "content-driven flip; separable" for all three, and every knockout lies outside its null.
- The rule's conditions, which would give (b) without the gate:
  - Deception drop passes: 1.000 vs 1.000.
  - The honest-answer drop fails on honest_instruction, where F -0.680 > D -0.682. It passes on no_pressure, where F -0.788 <= D -0.777.
  - Collateral fails: F 4.265 > D 0.327.
  - The nulls pass.
- Overlap: D/F Jaccard 0.340 heads (33 shared; 48 vs 82 heads) and 0.166 fine units.
- Delta table: the leaf cells D-F, D-H-F and F-D-H read "positional default" in the flip-audit column, with their head versions marked primary and reading "content-driven flip".
- Caveats:
  - The atomic knockouts saturate (D 0.000, F 0.000).
  - Both honest rows are non-discriminating at n=1000: |F - D| is 0.002 against an SE of 0.016, and 0.011 against 0.013.
  - F trained on 99% honest-split instances (train 149/150), and the F data is not instance-paired with D data (98% of its test set is from the honest split).
  - F is oversized at NLS 0.3 (+71% heads, +139% fine units). Its retune to 0.4 failed the in-run gate (KL 0.214; still +50% heads, +97% fine units); NLS 0.3 is carried.

**A FAR observation, not a writer issue.** Under the fixed prompt derivation (ticket 01), FAR's full model still gives the deceptive answer under both variants: 0.839 with the honest instruction and 0.871 with no pressure. Every knockout lowers that to between 0.08 and 0.17. So the honest-answer drops on D data are negative: the knockouts make the model more honest on the variant rows. In the 2026-09-22 rerun, before the fix, the full model was 0.106 / 0.058 there.

**SDR fine, verdict (c), and SDR coarse, verdict (a).** These are unchanged from the SDR round above. The fine suite's gate line now also reads: "Wikitext KL/token of every knockout: D 1.383 (FAILS), H 0.694 (FAILS), F 1.342 (FAILS)."

`tests/test_format_control_summary.py` passes 57 of 57 in both envs. Status is resolved. The independent-review box is the orchestrator's.
