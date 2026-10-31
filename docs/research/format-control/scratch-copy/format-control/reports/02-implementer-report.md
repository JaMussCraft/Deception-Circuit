# Ticket 02 implementer report: `nopressure` condition and glossary

Branch `format-control-02` (worktree `Deception-Circuit/.claude/worktrees/format-control-02`),
cut from `format-control` at 5b61031.

| commit | subject |
| --- | --- |
| c1c1f39 | Register nopressure as a third deception condition so Format Circuits train and evaluate like honest runs |
| e194874 | Test the composed-circuit condition label so D-F deltas show each operand's condition |

## What was implemented

- **One enumeration.** `tasks/__init__.py` gains `DECEPTION_CONDITIONS = ["deceptive", "honest", "nopressure"]`, next to `DECEPTION_TASKS`. `train.py --deception-condition` takes its `choices` from it.
- **Dataset directory.** `DeceptionTask.dataset_dir` maps `deceptive` to `<data-dir>/<task>` and every other condition to `<data-dir>/<task>_<condition>`. No third literal branch. An unknown condition now raises `ValueError` instead of silently loading `<task>`. A missing or `None` condition still means `deceptive`, as before.
- **Slug.** `run_io.build_run_slug` appends the condition whenever it is not `deceptive`, at the position `honest` used. A default far run gives `nls0.3_nopressure_noedge_<stamp>`, verified empirically by the end-to-end test. The honest slug is unchanged.
- **Help text.** The `--deception-condition` help and the `train.py` module docstring name `<task>_nopressure` and the Format Circuit.
- **Condition printing.** `evaluation/circuits.py` gains `condition_of(config_or_args)` and `circuit_condition(spec)`. The first returns `-` for tasks without a condition. The second reads each operand's `config.json`, giving `nopressure` for an atomic circuit and `D:deceptive,F:nopressure` for a composed one. The dry-run CIRCUITS and TASKS lines print `condition=...`. The suite banner prints `F [condition=nopressure]` for each bound circuit and `far [condition=nopressure]` for each task. `CircuitSpec` and `TaskSpec` are unchanged. `suite.json` already records each task's `deception_condition` through `_DATASET_KEYS`.
- **Warning text.** In `evaluation/context.py`, the "condition not recorded" warning and its comment now name `nopressure` alongside `honest`. There is no logic change.
- **CONTEXT.md.** A **Format Circuit** entry follows **Honest Twin** under Task structure, using the ticket's wording, with _Avoid_: control circuit, template circuit. **Honest Condition** gains a note separating the Honest Twin from the `nopressure` condition. **Pressure Clause** gains one sentence saying only the `nopressure` condition deletes it. Without that sentence, its claim that the clause is present in both conditions would contradict the new condition. "control" appears only under _Avoid_.

### Interpretation choices

- **"The suite summary prints the condition."** No existing writer in `report.py` or `suite.py` prints "honest" or any condition. I read the requirement as the suite banner at the top of `suite.log`, plus the dry-run plan. The `evaluation_summary.md` writer belongs to ticket 05, and it can call `condition_of` and `circuit_condition`.
- **No evaluator change was needed for `--task-from`.** `_DATASET_KEYS` and `_RUN_CONFIG_KEYS` already carry `deception_condition`. The end-to-end test confirms this resolves to `far_nopressure`.

## TDD evidence

The seams come from the ticket and the spec's Testing Decisions; the user was not consulted further.

1. **`dataset_dir` mapping.** `test_dataset_dir_follows_the_condition` is parametrized over all three conditions. `test_dataset_dir_refuses_an_unknown_condition` is new.
   - RED, mgnp: `pytest tests/test_deception_tasks.py -k dataset_dir` gave `4 failed, 6 passed`. The three `nopressure` cases failed and the unknown condition raised nothing (`DID NOT RAISE ValueError`).
   - GREEN: `1 failed, 35 passed`. The one failure is the baseline `test_hyperparameters_are_identical_across_the_three_mechanisms`.
2. **`train.py` parsing, help, slug and config.** The CLI and config tests are parametrized over `honest` and `nopressure`. `test_run_slug_separates_the_conditions` asserts the `nls0.3_{,honest_,nopressure_}noedge_` prefixes. `test_train_cli_help_names_the_format_circuit` is new.
   - RED: `4 failed, 3 passed`, with `invalid choice: 'nopressure' (choose from deceptive, honest)`.
   - GREEN: `1 failed (baseline), 38 passed`.
3. **End-to-end training run.** This is `tests/test_nopressure_condition.py::test_train_on_nopressure_writes_the_condition_and_the_slug`. It uses a 2-layer random Llama with the `TINY` geometry from `tests/helpers.py` and the vocabulary widened to `FAKE_VOCAB_SIZE`. The data is synthetic: a 6-record `far` and a 4-record `far_nopressure` with `condition: "nopressure"` and `margin_thresh 0.5`. The run is one node epoch with no edge pruning, with `train.main()` run from `tmp_path`.
   - First run failed on a test bug. The real slug was `ne1_bs2_seq96_nls0.3_nopressure_noedge_261013-195114`, because the test's small-run overrides come first. I fixed the regex to `fullmatch` that exact shape.
4. **`--task-from` resolution.** This is `test_task_from_a_nopressure_run_resolves_the_nopressure_test_set`. It resolves the trained run as both `--circuit F=` and `--task-from`.
   - Already green without changes: `deception_condition` is `nopressure`, `dataset_dir` gives `.../far_nopressure`, and the loader yields 4 records, not 6, with margin 0.5.
   - RED was the dry-run assertion `condition=nopressure` in the CIRCUITS block. GREEN came after the `dry_run` change.
5. **Suite banner.** This is `test_suite_banner_names_the_condition_of_each_circuit_and_task`, a real sanity-only suite on the trained run.
   - RED: the banner showed `circuits  F` and `tasks  far` with no condition. GREEN came after the `suite.run` change.
6. **Margin and runtime filter.** These tests passed on first run, because the path has no condition branch. They characterise existing behaviour rather than drive new code.
   - `test_margin_for_nopressure_defaults_to_the_dataset` checks that the dataset's `margin_thresh` (0.5) is the default and `--deception-margin-loss 0.25` overrides it.
   - `test_runtime_filter_applies_to_nopressure_as_to_honest` uses margin 1000. Without `--deception-runtime-filter`, val and test have 4 records each. With it, they have 0, because no logit gap of the random model reaches that margin. Train stays at 4.
7. **Composed-circuit label.** `test_a_composed_circuit_names_each_operands_condition` is a characterisation test added after the implementation, during self-review.

## Test results (full suite, both envs)

Commands as in `00-baseline-failures.md`, run at c1c1f39. The composed-circuit test, added afterwards in e194874, was run on its own file in both envs: 8 passed in mgnp, and all of its file passed in base.

| env | result | new failure names |
| --- | --- | --- |
| login base (py3.9, transformers 4.57.3) | 8 failed, 601 passed, 20 skipped | none |
| mgnp (py3.12, transformers 5.13) | 8 failed, 602 passed, 19 skipped | none |

The 8 failure names in each env are exactly the 8 baseline names.

## Files changed

`CONTEXT.md`, `evaluate_circuit.py`, `evaluation/circuits.py`, `evaluation/context.py`, `evaluation/suite.py`, `run_io.py`, `tasks/__init__.py`, `tasks/deception.py`, `train.py`, `tests/test_deception_tasks.py`, `tests/test_nopressure_condition.py` (new).

Ticket 01's files are untouched: `evaluation/variants.py`, `dataset/deception_common.py`, `dataset/build_*` and `tests/test_variants.py`.

## Self-review findings

- `circuit_condition` re-reads each operand's `config.json`, which `load_operands` already loaded. This is a small duplicate read, accepted so that `CircuitSpec` stays unchanged while tickets 04 and 05 edit nearby code.
- `dataset_dir` now raises on an unknown condition. Before, any unrecognised string silently loaded `<task>`. Only argparse-validated values are ever recorded in `config.json`, so no existing run is affected.
- The `evaluation/context.py` missing-condition warning still fires only for `far`/`sdr`/`ser`, not `joint`. This is pre-existing and unchanged.

## Concerns and things left alone

- **`dataset/deception_comparison_set.py`** still has `--condition choices=["deceptive","honest"]`. A `nopressure` comparison set needs all three tasks, and SER is deferred, so it would always stop with "Not built yet". I left it unchanged; widen it when SER `nopressure` exists.
- **`scripts/train_deception.sbatch` and `train_joint.sbatch`** mention `--deception-condition honest` only in usage comments and pass flags straight through to `train.py`. `nopressure` works through them unchanged, so they are untouched.
- **`--task joint --deception-condition nopressure`** would need `ser_nopressure`. It fails with the usual "build the dataset first" error, which is correct behaviour and needs no special case.
- **Pressure evaluation on `nopressure` tasks.** For ticket 04, a cell whose task comes from `--task-from <nopressure run>` reaches the pressure evaluation with no clause left to delete. Whether that cell skips or fails depends on ticket 01's variant helper; the spec says no variant rows are derived. Nothing in this ticket changes that path.
- **Shared worktree pin.** The EnterWorktree pin was shared with impl-01 and flipped repeatedly during the session. I re-pinned before each write and used absolute paths. All edits and both commits are on `format-control-02`, verified with `git branch --show-current` before each commit. impl-01 and the orchestrator were warned.
- **Independent review** is owned by the orchestrator, so its checkbox is left unticked.
