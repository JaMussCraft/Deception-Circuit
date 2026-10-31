# 02 — `nopressure` as a third `--deception-condition`, plus the glossary entry

**What to build:** Make `nopressure` a first-class condition everywhere `honest` already is, so a Format Circuit trains with `train.py --deception-condition nopressure` and its run directory serves as `--task-from` for the no-pressure test set in the evaluator. Add "Format Circuit" to `CONTEXT.md`.

**Status:** resolved
**Type:** task
**Blocked by:** None (can run in parallel with 01; ticket 03 needs both)

**Facts to build on**
- `tasks/deception.py:27-31` `dataset_dir`: two-branch suffix (`""` / `"_honest"`).
- `train.py:123-127`: `--deception-condition` with `choices=["deceptive", "honest"]`; the config written to `config.json` records `deception_condition`.
- `evaluation/circuits.py:38`: `--task-from RUN_DIR` inherits `deception_condition` from the run's `config.json`, so no evaluator change should be needed beyond accepting the new value wherever the two are enumerated (grep `"honest"` in `evaluation/` and `tasks/`).
- Slug convention: `nls0.3_honest_noedge_<stamp>`; the new one is `nls0.3_nopressure_noedge_<stamp>` (check where the slug is composed in `train.py` / `run_io.py`).

- [x] `dataset_dir` maps `nopressure` to `<data-dir>/<task>_nopressure`; `train.py` accepts the choice and composes the `_nopressure` slug; the help text names the Format Circuit.
- [x] Every place that enumerates conditions (`evaluation/`, `tasks/`, `run_io.py`, summary writers in `evaluation/report.py` or `suite.py` that print "honest") handles `nopressure` without special casing; the suite summary prints the condition for each bound circuit and task.
- [x] `--deception-runtime-filter` and `--deception-margin-loss` behave for `nopressure` as for `honest` (the dataset's `margin_thresh` is the default).
- [x] `CONTEXT.md`: a **Format Circuit** entry under task structure ("the circuit pruned on a mechanism task's `nopressure` condition: the Scaffold with the Pressure Clause deleted and honest labels; what the task format recruits absent any motive to deceive"; _Avoid_: control circuit, template circuit); a note under **Honest Condition** distinguishing the Honest Twin (pressure present, model honest) from the `nopressure` condition (pressure absent); "control" stays under _Avoid_.
- [x] Tests: `dataset_dir` mapping for all three conditions; `train.py` argument parsing accepts `nopressure`; an end-to-end run on the 2-layer random Llama (`tests/helpers.py`, `tests/test_end_to_end.py` pattern) with a synthetic `<task>_nopressure` directory trains and writes `config.json` with `deception_condition: "nopressure"`; `--task-from` on that run directory resolves the `_nopressure` test set.
- [x] Both suites in both envs; failure names vs baseline.
- [x] Independent review (orchestrator-dispatched; approved, no Critical/Important); report in `reports/02-nopressure-condition-and-glossary-review.md`.

## Comments

2026-10-13, implementer (impl-02). Branch `format-control-02`: c1c1f39 (registration, condition printing, glossary), e194874 (composed-circuit label test). Full report: `reports/02-implementer-report.md`.

- Built: `DECEPTION_CONDITIONS` in `tasks/__init__.py` used by `train.py` choices; `dataset_dir` maps any non-deceptive condition to `<task>_<condition>` and rejects unknown ones; slug appends the condition (`nls0.3_nopressure_noedge_<stamp>`, verified by an end-to-end run); help text and docstring name the Format Circuit; the dry-run plan and the suite banner print `condition=` for every bound circuit and task (helpers `condition_of` / `circuit_condition` in `evaluation/circuits.py`, available to ticket 05's writer); missing-condition warning in `evaluation/context.py` mentions `nopressure`. `--task-from` needed no change.
- Files: `CONTEXT.md`, `evaluate_circuit.py`, `evaluation/circuits.py`, `evaluation/context.py`, `evaluation/suite.py`, `run_io.py`, `tasks/__init__.py`, `tasks/deception.py`, `train.py`, `tests/test_deception_tasks.py`, `tests/test_nopressure_condition.py` (new). Ticket 01's files untouched.
- Tests at c1c1f39: login base 8 failed / 601 passed / 20 skipped; mgnp 8 failed / 602 passed / 19 skipped. The 8 failure names in both envs are exactly the baseline's; no new failures. The test added in e194874 was run on its own file in both envs and passes.
- Interpretation: "suite summary prints the condition" is implemented as the suite banner (top of `suite.log`) and the dry-run plan; the `evaluation_summary.md` writer is ticket 05's.
- Left alone, by design: `dataset/deception_comparison_set.py` still offers only deceptive/honest (a `nopressure` set needs SER, which is deferred); sbatch scripts only mention conditions in comments and pass flags through.
- No Slurm jobs (none needed).
- Independent review: owned by the orchestrator, checkbox left unticked.
