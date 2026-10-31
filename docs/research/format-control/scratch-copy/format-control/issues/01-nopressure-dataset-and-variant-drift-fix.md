# 01 — `<task>_nopressure` dataset builder and the variant drift fix

**What to build:** A clause-surgery helper that removes (or replaces) the stored Pressure Clause inside a stored prompt string; a builder that turns the stored deceptive FAR and SDR datasets into `far_nopressure` and `sdr_nopressure` (honest labels, both-streams behavioral filter with flip, stepped threshold, strict instance pairing, filter report); and the switch of `evaluation/variants.py` to the same helper so eval-time variants stop re-templating.

**Status:** resolved
**Type:** task
**Blocked by:** None

**Why first:** nothing trains before the dataset exists, and the drift fix changes every eval 2 / eval 4 variant row the later suite will read.

**Facts to build on**
- Stored records (`data/datasets/{far,sdr}`, arrow DatasetDict, splits train 200 / validation 200 / test 1000) carry `pressure` (clause text), `clean_prompt`, `corrupt_prompt`, `target`, `distractor`, `instance_id`, `pressure_id`, `desig`, `desig_inv`, `item_pair`, `item_polarity`, `designation_polarity`, `template_variant`, margins.
- `dc.rebuild_prompt(spec, rec, rec["pressure"])` reproduces 0/200 stored FAR prompts and 0/200 SDR prompts (200/200 SER): the stored FAR uses `ready`/`delayed`, the current `SPECS["far"]` uses weak/strong plus a suffix sentence. `evaluation/variants.py:deception_records` (consumed by `evaluation/pressure.py` and `evaluation/context.py`) therefore builds mismatched variant prompts for FAR and SDR today.
- `dataset/deception_common.py`: `filter_by_model_behavior` (keeps clean argmax == target at margin AND corrupt argmax == distractor at margin), `evaluate_behavior`, `harvest_honest_twins`, `assert_aligned_pair`, `HONEST_INSTRUCTION`, `MAX_SEQ_LENGTH`. `dataset/build_deception_dataset.py` has the save/report conventions (`save_splits`, `pass_rate_tables`, `filter_report.json`, `dataset_config.json`).
- Honest-twin instances are disjoint from the deceptive ones (0 shared test ids).

- [x] `dataset/clause_surgery.py` (or a section of `deception_common.py`): `remove_clause(prompt, clause)` and `replace_clause(prompt, clause, replacement)`; each asserts the clause is non-empty and occurs exactly once, and removes it with its single leading space; the helper is tokenizer-free.
- [x] `evaluation/variants.py:deception_records` derives `no_pressure` and `honest_instruction` prompts from the stored `clean_prompt` / `corrupt_prompt` with the helper (replacement `dc.HONEST_INSTRUCTION`), keeps `assert_fits` and `assert_aligned_pair`, and no longer calls `dc.rebuild_prompt` / `dc.build_prompt`. When the dataset's `condition` is `nopressure` (the `pressure` field is empty), `deception_records` derives no variants and returns an empty list with the reason recorded in the cell output: that dataset already is the no-pressure variant and has no slot for an honest instruction. `std_records` untouched. `tests/test_variants.py` updated; a test uses a stored-style FAR record with the old `ready`/`delayed` wording and asserts the variant equals the stored prompt minus the clause.
- [x] `dataset/build_nopressure_dataset.py --task {far,sdr}`: loads `<data-dir>/<task>`, relabels every record (swap `target`/`distractor`, `condition: "nopressure"`, `pressure: ""`, keep `pressure_id` and `instance_id`), rewrites both prompts with the helper, re-asserts alignment, runs `evaluate_behavior` once per split on the full model, and applies `filter_by_model_behavior`'s rule offline at thresholds 0.7, 0.5, 0.3 in order, choosing the first that yields >= 150 train and >= 500 test; floor 0.3; `--min-train`, `--min-test`, `--thresholds` are flags with those defaults.
- [x] Fallback: if the minimums still fail at the floor, the honest dataset's instances (`<task>_honest`, same clause surgery, labels already honest) are filtered the same way and appended with `source: "honest_split"`; every record from the deceptive splits carries `source: "deceptive_split"`. Validation follows the train rule (>= 150) for the fallback decision.
- [x] Output: `<data-dir>/<task>_nopressure/` with the same DatasetDict layout as `<task>_honest`, `dataset_config.json` (`condition: "nopressure"`, chosen `margin_thresh`, `thresholds_tried`, `source_counts`, `created`), `filter_report.json` with per-threshold survivor counts per split, pass rates by item pair, item polarity, designation polarity and template variant, unexpected-argmax counts, margin distributions, the fallback subset size, and three sampled clean/corrupt pairs for inspection.
- [x] `scripts/build_nopressure.sbatch` mirroring `scripts/build_far.sbatch`; `--no-model` dry path on the login node exercises everything but the forward passes.
- [x] Tests with `tests/fakes.py` (fake tokenizer, scripted model): clause removal and replacement (once, twice, absent, empty clause refused, leading-space handling, alignment preserved); `deception_records` on a `nopressure` record yields no variants and states why; relabel swap; threshold step-down picks the first passing threshold and records every step; fallback appended and tagged only when minimums fail; config and report fields present.
- [x] The built `<task>_nopressure` DatasetDicts are committed on the branch like `<task>_honest` (about 1,400 records each), so later tickets and `--task-from` find them from any worktree.
- [x] Built on a GPU for FAR and SDR; `filter_report.json` numbers quoted in Comments (chosen threshold, survivors per split, fallback size, polarity and item mix).
- [x] Both test suites run in both envs, failure names compared to the branch-base baseline.
- [x] Independent subagent review against the spec (orchestrator-dispatched; approved, no Critical/Important); report in `reports/01-nopressure-dataset-and-variant-drift-fix-review.md`; findings addressed or listed.

## Comments

- 2026-10-13 19:59 CDT: submitted GPU build job **22878917** (`scripts/build_nopressure.sbatch`, FAR then SDR; account beto-delta-gpu, partitions gpuA40x4,gpuA100x4,gpuA100x8,gpuH200x8, --time 00:30:00) from the format-control-01 worktree root.
- Job 22878917 COMPLETED in 00:05:58 on gpuA40x4. Log: `Deception-Circuit/.claude/worktrees/format-control-01/logs/build_nopressure_22878917.out` (untracked, `logs/` is ignored).

### Researcher decisions and findings (read first)

1. **Finding: FAR "deceptive" behaviour is designation-following, not pressure-driven.** The stored FAR deceptive dataset is 100% `designation_polarity: "identity"` (train 200/200, validation 200/200, test 1000/1000; `far_honest` is mixed, train 130/70 and test 671/329). FAR's behavioral filter kept only instances where the deceptive answer equals the designated item. Those instances answer the same way with the Pressure Clause deleted: under honest labels the median clean margin is -1.12 (p75 -0.5, p95 +0.5), with zero off-pair argmax tokens. Only 9 of 1,400 deceptive-split instances pass the honest both-streams filter even at the 0.3 floor (train 1, validation 0, test 8). This is consistent with the spec's note that the empty circuit's no-pressure logit difference on FAR is already +1.98. The per-threshold counts are on record in `far_nopressure/filter_report.json` (`per_threshold`) and `dataset_config.json` (`thresholds_tried`, `source_counts`).
2. **FAR F dataset composition.** The floor failed, so the pre-registered fallback applied. `far_nopressure` is 150 / 150 / 500, of which 791 of 800 records are `source: "honest_split"`: train 1 + 149, validation 0 + 150, test 8 + 492 (deceptive_split + honest_split). The FAR F column is therefore essentially unpaired with D. Orchestrator ruling (2026-10-13): commit as built, train on it, and mark the F-data column unpaired in ticket 05.
3. **SDR composition and polarity drift.** `sdr_nopressure` is 150 / 150 / 520 at margin 0.3 (thresholds 0.7 / 0.5 / 0.3 gave train 90 / 101 / 106, validation 87 / 92 / 96, test 470 / 500 / 520; none met train and validation >= 150). Deceptive-split survivors are 106 / 96 / 520, topped up with 44 train and 54 validation honest-split records, and the test split is fully paired. Pass rate by designation polarity is inversion 550/596 against identity 172/804, so survivors drift toward inversion: test is 393 inversion / 127 identity, against 431 / 569 in the stored SDR test split.
4. **Validation minimum.** The step-down and the fallback both apply the train minimum to validation (minimums 150 / 150 / 500). The ticket's step-down sentence names only train and test, but its fallback sentence says validation follows the train rule; one rule for both was the coherent reading. Train and validation have the same pool size (200), so the difference is small. In both builds no threshold met the minimums anyway.
5. **Fallback top-up size.** Each short split is topped up only to its minimum, in `instance_id` order, so the unpaired subset stays as small as possible. The result is 800 / 820 records instead of the ticket's "about 1,400". Appending every honest-split survivor would give FAR about 1,375 records (all but 9 unpaired) and SDR 1,113 (train 303, validation 290, test 520 unchanged). Your call if you prefer larger datasets.
6. **Neutral prompts and prior margins.** The clause is also cut from `neutral_prompt`, so the record stays self-consistent. `prior_margin` is carried over from the source build, which measured it on the with-pressure neutral prompt; `dataset_config.json` says so in `prior_margin_note`. `clean_margin` and `corrupt_margin` are this build's values under honest labels.
7. **Stored SDR wording.** Stored SDR prompts have no space before the suffix sentence ("...harmless.THE DAMAGING ONE..."). This is inherited from the stored data and not touched here; clause surgery only removes the clause and its own leading space.
8. **Empty-variant skip reason (orchestrator ruling).** An empty variant set becomes `(None, reason)` in `evaluation/context.py` `Session.variant_loader`, because the metrics divide by n. The reason is read from the dataset: `dataset_config.json` `condition`, else every test record having an empty `pressure`. It never comes from `args.deception_condition`. `tasks/deception.py` is untouched.

### What was built

- `dataset/clause_surgery.py`: tokenizer-free `remove_clause` and `replace_clause`. Each raises `ValueError` on an empty clause, a clause occurring 0 or 2+ times, or a clause with no leading space. `replace_clause` also refuses an empty replacement.
- `evaluation/variants.py`: `deception_records` derives both variants from the stored strings by clause surgery and no longer calls `dc.rebuild_prompt` / `dc.build_prompt`. A nopressure test set returns `[]` and prints the reason; a test set mixing nopressure and pressured records raises. New `dataset_is_nopressure` and `empty_variant_reason`. `std_records` is untouched.
- `evaluation/context.py`: the empty-variant guard (a few lines in `Session.variant_loader`).
- `dataset/deception_common.py`: `behavior_passes(behavior, margin_thresh)`, extracted from `filter_by_model_behavior`, which now calls it (no behaviour change).
- `dataset/build_nopressure_dataset.py`: the builder (relabel, surgery, alignment, one behavior pass per split for both the deceptive and honest splits, offline step-down, fallback, report, config).
- `scripts/build_nopressure.sbatch`: runs FAR then SDR; `--no-model` was rehearsed on the login node for both tasks, with all 2,800 records per task (deceptive and honest) passing surgery and alignment on the real Llama tokenizer.
- Tests: `tests/test_clause_surgery.py` (new), `tests/test_build_nopressure.py` (new), `tests/test_variants.py` (drift, nopressure and skip-reason tests added).
- Data: `data/datasets/far_nopressure/`, `data/datasets/sdr_nopressure/` (DatasetDict plus `dataset_config.json` and `filter_report.json`). Verified: every record's `instance_id` is in its source split (deceptive or honest) of the same name, no duplicates, `pressure` empty, `condition` nopressure, columns equal `<task>_honest` plus `source`, minimum margin 0.375.

### Tests

| env | result | new failure names |
| --- | --- | --- |
| login base (py3.9, transformers 4.57.3) | 8 failed, 621 passed, 20 skipped | none |
| mgnp (py3.12, transformers 5.13) | 8 failed, 622 passed, 19 skipped | none |

The 8 failing names are identical in both envs and identical to `reports/00-baseline-failures.md`.

### Commits

- 84c353b and a922f5d were made by impl-01 directly.
- Later commits, including the built datasets, are made by the orchestrator on impl-01's instruction, because only the orchestrator runs git (shared worktree pin).

### Open

- Datasets committed as 31291cb by the orchestrator on impl-01's instruction (24 files: the two `<task>_nopressure` directories). Sizes are 800 (FAR) and 820 (SDR) records, not the ticket's estimate of about 1,400; see decision 5.
- The independent review checkbox is owned by the orchestrator, who dispatches the reviewer.
- Full report: `Alignment/.scratch/format-control/reports/01-implementer-report.md`.
