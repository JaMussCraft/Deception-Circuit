# Review: ticket 01, `<task>_nopressure` dataset builder and variant drift fix

Reviewer: review-01 (independent subagent). Date: 2026-10-13.
Diff: base 5b61031, head 31291cb on `format-control-01`. The commits are 84c353b, a922f5d and 31291cb.
Inputs: the ticket and its Comments, the spec's Implementation Decisions and Testing Decisions, the implementer report, the diff package, and the built `{far,sdr}_nopressure/{dataset_config.json,filter_report.json}`.

## Spec Compliance

| requirement | verdict |
| --- | --- |
| `remove_clause` / `replace_clause` refuse an empty clause, require exactly one occurrence, remove the single leading space, tokenizer-free | ✅ `dataset/clause_surgery.py:22-53`. It is stricter than the spec because it also refuses a clause with no leading space and an empty replacement. It refused nothing on any stored record (see Strengths). |
| Result passes `assert_aligned_pair` | ✅ The builder re-asserts at `build_nopressure_dataset.py` `derive_split`, and `variants.py` `deception_records` re-asserts too. Tests: `test_the_surgered_pair_stays_aligned`, `test_derived_split_is_aligned`. |
| `deception_records` derives `no_pressure` / `honest_instruction` from the stored prompts with the helper and `dc.HONEST_INSTRUCTION` | ✅ In `evaluation/variants.py` `deception_records`, the loop body uses `remove_clause` / `replace_clause` on `clean_prompt` and `corrupt_prompt`. |
| It keeps `assert_fits` and `assert_aligned_pair` and no longer calls `dc.rebuild_prompt` / `dc.build_prompt` | ✅ Grep of the worktree: no `dc.rebuild_prompt` / `dc.build_prompt` caller is left under `evaluation/`. The remaining callers are `dataset/pilot_deception.py:149`, which is dataset-side, and the STD path `evaluation/variants.py:182-183` through `sl.rebuild_prompt`. Both are out of scope. `evaluation/pressure.py` and `evaluation/context.py` reach FAR/SDR/SER variants only through `deception_records`. |
| A nopressure dataset derives no variants, returns `[]` and records the reason | ✅ `deception_records` prints `_nopressure_reason` and returns `[]`. `evaluation/context.py` `Session.variant_loader` turns the empty loader into `(None, reason)`, and the reason is read from the dataset (`dataset_is_nopressure`), never from args. This matches orchestrator ruling 8 in the ticket Comments. |
| `std_records` untouched | ✅ No hunk touches it. |
| Drift test: stored-style FAR record, old `ready`/`delayed` wording, variant equals the stored prompt minus the clause | ✅ `tests/test_variants.py` `test_no_pressure_variant_is_the_stored_prompt_minus_the_clause` asserts equality with `record["clean_prompt"].replace(" " + STORED_CLAUSE, "")` for both streams. It also asserts that the `ready ... delayed.<|eot_id|>` text survives and that `weak` is absent. The record carries `entity` / `item_1` / `item_2` / `template_variant`, so the old `rebuild_prompt` path would have run and produced weak/strong wording. The implementer's RED output (`'...at is weak is' == '...is delayed is'`) is consistent with that. `test_honest_instruction_variant_replaces_the_stored_clause_in_place` covers the other variant. |
| Builder relabel: swap target/distractor, `condition: "nopressure"`, `pressure: ""`, keep `pressure_id` and `instance_id` | ✅ `nopressure_record`. Tested with an independent oracle (`honest_answer`) for both designation polarities. |
| Rewrite both prompts and re-assert alignment | ✅ `neutral_prompt` is cut as well, which is disclosed and harmless. |
| `evaluate_behavior` once per split; offline rule at 0.7 / 0.5 / 0.3; first threshold with >= 150 train and >= 500 test; floor 0.3; `--min-train`, `--min-test`, `--thresholds` flags | ✅ with a recorded deviation. `select_threshold` and `_check_thresholds` refuse non-descending input and anything below the floor. `dc.behavior_passes` is extracted from `filter_by_model_behavior`, so the rule is shared, not copied. **Deviation:** validation must also reach the train minimum in the step-down, not only in the fallback (Comments item 4). It had no effect on the outcome: SDR train was below 150 at every threshold (90 / 101 / 106), and FAR passed nothing. |
| Fallback from `<task>_honest` tagged `honest_split` only when the minimums fail; validation follows the train rule; deceptive records tagged `deceptive_split` | ✅ with a recorded deviation. `assemble` filters the honest twin at the chosen (floor) threshold. **Deviation:** each short split is topped up only to its minimum, in `instance_id` order, rather than with every honest survivor. That gives 800 (FAR) and 820 (SDR) records against the ticket's "about 1,400" (Comments item 5). This is the researcher's call and is left open in the ticket. It is not re-litigated here. |
| Output layout identical to `<task>_honest` | ✅ Both have `train/ validation/ test/ dataset_dict.json dataset_config.json`, and `_nopressure` adds `filter_report.json`. `dataset_dict.json` is identical. |
| `dataset_config.json`: `condition`, `margin_thresh`, `thresholds_tried`, `source_counts`, `created` | ✅ Present in both built configs (checked on disk). |
| `filter_report.json`: per-threshold survivors per split, pass rates by item pair / item polarity / designation polarity / template variant, unexpected-argmax counts, margin distributions, fallback size, three sampled pairs | ✅ All present in both built reports. Two Minor gaps are listed below. |
| `scripts/build_nopressure.sbatch` mirrors `build_far.sbatch`; `--no-model` dry path | ✅ Same header, env activation and log layout. The only changes are the job name, time, task loop and builder. `test_no_model_dry_run_writes_nothing` covers the dry path. |
| Tests use `tests/fakes.py` and cover the listed behaviours | ✅ Covered: removal and replacement, once / twice / absent / empty, leading space, alignment, the nopressure no-variant case with its reason, relabel, step-down records every step, fallback tagged only on failure, and config and report fields. The tests use `FakeWordTokenizer` and `ScriptedModel` through the real `dc.evaluate_behavior`. |
| Shared-file changes minimal and additive; ticket 02's files untouched | ✅ The diff stat touches none of `tasks/deception.py`, `train.py`, `run_io.py`, `evaluation/circuits.py` or `CONTEXT.md`. `deception_common.py` changes by extraction only, `context.py` gains 11 lines, and `variants.py` changes only `deception_records` plus two new helpers. |
| Both suites in both envs, failure names compared to the baseline | ⚠️ Not re-run, per the brief. The reported counts are consistent with the change. Base went from 584 to 621 passed and mgnp from 585 to 622, which is +37 in each. That equals the new tests (12 clause surgery + 14 builder + 11 variants). Skips are unchanged at 20 and 19. The 8 failing names are reported identical to `00-baseline-failures.md`. |
| Orchestrator ruling on FAR recorded | ✅ Ticket Comments item 2 records it. On disk, `far_nopressure/dataset_config.json` `source_counts.test` is `{deceptive_split: 8, honest_split: 492}` and SDR's is `{520, 0}`, so the "unpaired by data" test in the implementer report holds. |
| Report numbers match the ticket Comments | ✅ FAR per-threshold counts are (0,0,1) / (0,0,3) / (1,0,8). Honest-split counts at 0.3 are 196 / 193 / 977. The fallback adds 149 / 150 / 492 (791 total). The deceptive-split clean margin is p50 -1.125, p75 -0.5 and p95 +0.5. Template `lab` passed 0/60. SDR counts are 90/101/106, 87/92/96 and 470/500/520. SDR passes are inversion 550/596 and identity 172/804. The SDR test split is 393 inversion / 127 identity, and the top-up adds 44 / 54. There are no unexpected argmax tokens in either task. Everything matches. |

## Strengths

- **Surgery checked against all stored data, not only FAR/SDR.** The reviewer ran `remove_clause` and `replace_clause` over every record of `far`, `sdr`, `ser` and their honest twins. That is 2,864 records and both streams, and it produced zero refusals. The SER eval variants, which now also go through surgery, therefore do not regress.
- **The filter rule is shared, not copied.** `dc.behavior_passes` is extracted, and `filter_by_model_behavior` calls it with no behaviour change. The offline step-down reuses the exact rule.
- **The drift test is a real regression test.** It fails on the old code path (RED evidence) and pins the stored wording.
- **Clear refusals.** The helper refuses every ambiguous case with a message that shows the clause and the prompt. `deception_records` refuses a test set that mixes nopressure and pressured records instead of silently picking one.
- **The skip reason comes from the data**, from `dataset_config.json` `condition` or else all-empty `pressure`, never from run arguments. The metrics cannot divide by zero on an empty variant loader.
- **The provenance is good.** `source` on every record, `source_counts`, `source_datasets` with repo-relative paths, `honest_split_per_threshold` and `prior_margin_note` make the FAR fallback auditable.
- **The top-up did not skew polarity.** The FAR test `survivor_mix` is 339 identity / 161 inversion against the honest pool's 671 / 329.

## Issues

### Critical

None.

### Important

None for ticket 01. The first Minor item needs an explicit decision in ticket 03 and is escalated there.

### Minor

1. **The task margin carries over into training (cross-ticket, escalate to ticket 03).** `build_config` writes `margin_thresh: 0.3`, as the ticket requires. `tasks/deception.py:41` passes the dataset config to `dc.resolve_margin`, which uses `margin_thresh` as the training hinge margin (`tasks/deception.py:99`) and the runtime-filter threshold whenever `--deception-margin-loss` is unset. The paired FAR runs `nls0.3_noedge_260819-083914` and `nls0.3_honest_noedge_260819-084020` have `deception_margin_loss: null`, so D and H trained at 0.7 from their configs. Left as is, F would train at 0.3. That breaks the spec's "Training. Identical to the paired run" and could move the head and unit counts the size rule compares. **Why it matters:** the D/F comparison would confound pressure with loss margin. **Fix:** in ticket 03, pass `--deception-margin-loss 0.7` explicitly for the F runs, or record a deliberate choice of 0.3 in the launcher. This is not a ticket 01 defect, because the key and its value are what the ticket asked for.
2. **Stale inherited config keys.** `build_config` spreads `**src_config`, so `train_samples: 200`, `val_samples: 200`, `test_samples: 1000`, `overgen_factor`, `seed`, `n_pressures` and `match_length_distribution` are copied unchanged. The size keys now misdescribe 150 / 150 / 500 (FAR) and 150 / 150 / 520 (SDR). No code reads them from `dataset_config.json`: the only consumer is `resolve_margin`, which reads `margin_thresh`. The impact is provenance only. **Fix:** nest the source config under `source_config`, or drop the generation-only keys.
3. **Duplicated unexpected-token counting.** `build_nopressure_dataset.py` `unexpected_tokens` repeats the Counter logic in `dataset/deception_common.py:972-978`. Only the report uses it, and the filter rule itself is shared, so a divergence cannot change which records are kept. **Fix:** extract it next to `behavior_passes` and call it from both places, if a wider shared-file change is acceptable.
4. **`_is_nopressure` treats a missing `pressure` key as nopressure.** In `evaluation/variants.py`, a record without the key gets `[]` with the nopressure message. Stored deception records always carry the key, and the implementer's self-review says so. **Fix (optional):** require `condition == "nopressure"`, or `pressure == ""` with the key present.
5. **The report describes the deceptive split, not the kept records.** The `pass_rate_by_*` tables, the per-split `clean_margin` / `corrupt_margin` and `unexpected_argmax_tokens` cover only the deceptive input. For FAR, 791 of 800 kept records are `honest_split`, whose margin distributions and unexpected tokens are not in `filter_report.json`. The implementer's "min margin 0.375, no unexpected tokens" check was ad hoc. Only `survivor_mix` and `honest_split_per_threshold` describe them. All three `sample_pairs` for FAR are `honest_split`, because they are drawn from the final train split. **Fix:** add a margin summary and unexpected-token count over the final kept records per split, and draw one sample pair per source when both are present.
6. **Design note, not a defect.** Honest splits are scored unconditionally, which doubles the forward passes. The cost was small (5:58 of GPU time) and it buys `honest_split_per_threshold`.

### Test output noise

The implementer report quotes no warnings. The reviewer's own scripts in the base env printed a pandas `UserWarning` saying bottleneck 1.3.5 is older than the required 1.3.6. That is environmental and unrelated to this change. The reviewer did not re-run the suites.

## Assessment

**Spec compliance: Approved.** Every acceptance criterion is met. The two deviations, the validation minimum in the step-down and the top-up-to-minimum fallback size, are disclosed in the ticket Comments, had no effect on threshold choice, and leave the size question open for the researcher.

**Task quality: Approved.** The code is small, refuses ambiguous input, shares the filter rule, and is tested at the seams the spec names. The drift test genuinely pins the fix. The remaining items are Minor. Item 1 needs an explicit margin decision in ticket 03's training launch.
