# Ticket 01 implementer report: `<task>_nopressure` builder and variant drift fix

Implementer: impl-01. Worktree `Deception-Circuit/.claude/worktrees/format-control-01`, branch `format-control-01`, base 5b61031.
Date: 2026-10-13.

## Outcome

Status: DONE_WITH_CONCERNS. Everything in the ticket is built, tested in both envs and built on a GPU. The concern is scientific, not code. FAR's no-pressure dataset is 791/800 honest-split fallback because FAR's deceptive instances are designation-following and do not depend on pressure. The orchestrator has ruled to commit it as built and mark the FAR F column unpaired.

## Findings the researcher must read

1. **FAR "deception" is designation-following, not pressure-driven.** The stored FAR deceptive dataset is 100% `designation_polarity: "identity"` (train 200/200, validation 200/200, test 1000/1000). The honest twin is mixed (train 130/70, validation 125/75, test 671/329). So FAR's behavioral filter kept only instances whose deceptive answer is the designated item. With the clause deleted, those instances still name the designated item:

   | FAR deceptive split, honest labels, no pressure | value |
   | --- | --- |
   | median clean margin | -1.12 |
   | clean margin p75 / p95 | -0.50 / +0.50 |
   | off-pair argmax tokens | 0 |
   | survivors at 0.7 / 0.5 / 0.3 (train, val, test) | (0,0,1) / (0,0,3) / (1,0,8) |

   This agrees with the spec's note that the empty circuit's no-pressure logit difference on FAR is +1.98.
2. **FAR F composition.** At the 0.3 floor, with the fallback applied, `far_nopressure` is train 1 + 149, validation 0 + 150 and test 8 + 492 (deceptive_split + honest_split). The honest-split survivors available were 196 / 193 / 977.
3. **SDR composition and drift.** At thresholds 0.7 / 0.5 / 0.3, train survivors were 90 / 101 / 106, validation 87 / 92 / 96 and test 470 / 500 / 520. No threshold met train and validation >= 150, so 0.3 was chosen and train and validation were topped up with 44 and 54 honest-split records. The test split, 520 records, is fully paired. By designation polarity, inversion passes 550/596 and identity 172/804. The `sdr_nopressure` test split is 393 inversion to 127 identity, while the stored SDR test split is 431 to 569.

## Decisions I made (please confirm or overrule)

- **Validation minimum.** Validation uses the train minimum in both the step-down and the fallback, giving minimums of 150 / 150 / 500. The ticket names only train and test for the step-down but says validation follows the train rule for the fallback. With one set of minimums the threshold choice and the fallback cannot disagree.
- **Top-up size.** The fallback tops each short split up to its minimum only, in instance_id order, which keeps the unpaired subset small. That gives 800 records for FAR and 820 for SDR, against the ticket's "about 1,400". Appending every honest-split survivor would give FAR 1,375 and SDR 1,113.
- **Neutral prompts and prior margins.** `neutral_prompt` also loses the clause. `prior_margin` is carried over from the source build, which measured it with pressure, and the config notes this. `clean_margin` and `corrupt_margin` are this build's values.
- **Honest splits are scored unconditionally** in the same job, so the report shows how much fallback was available even when it is not used (`honest_split_per_threshold`).
- **Empty-variant reason (orchestrator ruling).** `Session.variant_loader` in `evaluation/context.py` turns an empty variant loader into `(None, reason)`; without that, the metrics divide by zero. The reason comes from the dataset (`dataset_config.json` condition, else all-empty `pressure`), never from `args.deception_condition`. `tasks/deception.py` is untouched.

## What was implemented

| file | change |
| --- | --- |
| `dataset/clause_surgery.py` | new: `remove_clause`, `replace_clause` (tokenizer-free, refuse empty/absent/repeated clause, missing leading space, empty replacement) |
| `evaluation/variants.py` | `deception_records` by clause surgery; nopressure returns `[]` with printed reason; mixed sets raise; `dataset_is_nopressure`, `empty_variant_reason` |
| `evaluation/context.py` | empty-variant guard in `Session.variant_loader` |
| `dataset/deception_common.py` | `behavior_passes` extracted; `filter_by_model_behavior` calls it |
| `dataset/build_nopressure_dataset.py` | new builder |
| `scripts/build_nopressure.sbatch` | new, FAR then SDR, mgnp env |
| `tests/test_clause_surgery.py`, `tests/test_build_nopressure.py` | new |
| `tests/test_variants.py` | drift, nopressure and skip-reason tests |
| `data/datasets/{far,sdr}_nopressure/` | built datasets plus config and report |

Shared files touched: `evaluation/variants.py`, `evaluation/context.py` and `dataset/deception_common.py`, all with additive edits. None of ticket 02's files were touched.

## TDD evidence (base env)

| slice | RED | GREEN |
| --- | --- | --- |
| clause surgery | `ModuleNotFoundError: No module named 'dataset.clause_surgery'` | 12 passed |
| variants by surgery | 7 failed, 25 passed; drift shown as `'...at is weak is' == '...is delayed is'` (re-templated "weak" against stored "delayed") | 44 passed (variants + surgery) |
| builder | `ImportError: cannot import name 'build_nopressure_dataset'` | 14 passed |
| skip reason read from data | 3 failed, 31 passed | 60 passed (all three files) |

Command shape: `cd <worktree> && OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python -m pytest tests/<file> -q -p no:cacheprovider`.

The builder slice was not a strict vertical slice. Its tests were written together against the planned seams, then the module was written once.

## Test suites (final, after all code changes)

| env | result | new failure names |
| --- | --- | --- |
| login base | 8 failed, 621 passed, 20 skipped | none |
| mgnp | 8 failed, 622 passed, 19 skipped | none |

The failing names are identical in both envs and to `00-baseline-failures.md`. No `core.*` dumps were produced.

## GPU build

- Job 22878917: account beto-delta-gpu, partitions gpuA40x4, gpuA100x4, gpuA100x8 and gpuH200x8, `--time 00:30:00`. It backfilled at once onto gpuA40x4 and COMPLETED in 00:05:58.
- Before submitting, `--no-model` was rehearsed on the login node for FAR and SDR. All 2,800 records per task, deceptive and honest, passed clause surgery and alignment on the real Llama tokenizer.
- The log is `format-control-01/logs/build_nopressure_22878917.out`, which is untracked.

Post-build verification:

- Every record's instance_id lies in its source dataset's split of the same name.
- There are no duplicate ids.
- `pressure` is empty and `condition` is `nopressure` on every record.
- The columns equal `<task>_honest`'s plus `source`.
- The minimum margin in both streams is 0.375, at or above the 0.3 floor.
- Unexpected argmax tokens: none in either task.

`dataset_config.json` carries `condition`, `margin_thresh`, `met_minimums`, `thresholds`, `thresholds_tried`, `min_train`, `min_validation`, `min_test`, `source_counts`, `source_datasets` and `created`. `source_counts` has the shape `{split: {"deceptive_split": n, "honest_split": m}}`, so the F-data test column is instance-paired exactly when `source_counts["test"]["honest_split"] == 0`. That is true for SDR and false for FAR, which has 492. `source_datasets` paths are relative to the repo root (`data/datasets/far`, `data/datasets/far_honest`), so they hold from any worktree. FAR's honest-twin instances pass at 196/200, 193/200 and 977/1000 at 0.3. `filter_report.json` carries:

- `per_threshold` survivor counts per split
- `honest_split_per_threshold`
- per-split margins and unexpected tokens
- pass rates by item pair, pressure, entity, domain, designation polarity, item polarity and template variant
- `survivor_mix` per split
- `fallback`
- three sample pairs

Template mix: in FAR, the deceptive split's `lab` variant passes 0/60. In SDR, `audit` passes 524/1102 and `lab` 198/298.

## Self-review

- `deception_records` treats a record with a missing or empty `pressure` as nopressure. Stored deception datasets always carry `pressure`, so this only matters for hand-made records.
- `dataset_is_nopressure` falls back to the generic reason when the dataset cannot be read. That costs only the specificity of the message, never a crash.
- Margins are bf16 values, quantised to steps of 1/8, so the step-down boundaries fall on quantised values.
- From now on, eval 2 and eval 4 variant rows for FAR and SDR are computed on the stored wording. Earlier runs' variant rows remain suspect, as the spec says, and are not recomputed.
- The stored SDR prompts lack a space before the suffix sentence ("harmless.THE DAMAGING..."). That is inherited, not introduced.

## Commits

- 84c353b "Derive no-pressure prompts by clause surgery so FAR/SDR variants match the stored data" (impl-01).
- a922f5d "Read the nopressure skip reason from the dataset, not from the run's arguments" (impl-01).
- 31291cb "Add the far_nopressure and sdr_nopressure datasets so the Format Circuits can train", made by the orchestrator on impl-01's instruction (only the orchestrator runs git, because the worktree pin is shared).

## Not done here

The independent review belongs to the orchestrator.
