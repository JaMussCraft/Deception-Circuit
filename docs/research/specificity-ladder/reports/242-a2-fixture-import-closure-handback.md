# A2 fixture import closure

Status: handed-back

## What changed

No source files changed. This is a static import-closure inspection of the r4 fixture runner and its three GREEN test modules.

## How verified

The runner uses only standard-library imports (`task2/green-r4/run_cpu_green.py:2-11`) and invokes `pytest` for the three fixture files (`run_cpu_green.py:39-46`). The tests import standard-library modules and `pytest` (`candidate/tests/test_full_score_cpu.py:9-20`, `test_full_score_controller.py:6-18`, `test_full_score_entry198.py:6-11`). They dynamically load candidate modules from files: CPU validation/supervisor (`test_full_score_cpu.py:32-39`), GPU common/controller/host-launch (`test_full_score_controller.py:42-61`), and shared controller fixtures from the entry test (`test_full_score_entry198.py:11`). Those production module top-level imports are standard-library imports; controller imports `common` (`candidate/gpu/controller.py:2-10`).

The CPU tests replace the native boundary with an injected `SimpleNamespace` (`test_full_score_cpu.py:78-145`) and call `validate_native_context` (`test_full_score_cpu.py:148-170`). The only dynamic scientific import found, `component_analysis.a2_pipeline`, is inside `validate_full_score` (`candidate/cpu/validate-phase.py:305-322`); the fixture cases inspected do not call that function. No numpy, torch, transformers, or native-bank import is required by this fixture closure.

The runner explicitly targets `/sw/external/python/anaconda3/bin/python3.9` and the mgnp Python (`run_cpu_green.py:19`), records full interpreter and pytest versions (`run_cpu_green.py:98-101`), but checks only Python major/minor 3.9 and 3.12 (`run_cpu_green.py:102`). The tests do not assert an exact pytest or patch version. Therefore the suite has no explicit exact-Python-patch/package pin in its assertions, while the execution packet does explicitly select the BASE executable and both supported interpreter legs. This does not justify substituting another Python 3.9 environment for BASE.

Static path discrepancy: the runner computes `CANDIDATE` under `plan-plan-a2-full-score-operational186/candidate` and derives `TESTS` from it (`run_cpu_green.py:13-17`), while r4 `pins.json` names the test sources under sibling `plan-a2-full-score-operational186/candidate`, where the three modules are present. The computed r4 candidate/tests path is absent in this checkout. This is unresolved for the runner's effective test path.

## Execution evidence

No tests or runner were executed. No native imports, models, GPU work, or scientific execution occurred. This report makes no run-success or baseline-reproduction claim.

## What is NOT done

The computed-path discrepancy was not repaired or tested. Exact environment-version behavior was not experimentally compared; this is a static import and assertion audit only.

## Open questions

Root should reconcile the r4 runner's computed candidate path with its pinned test-source paths before relying on the GREEN command.

## Correction

The preceding path-discrepancy claim and open question are withdrawn. I misread the runner's path expression and checked the wrong derived directory. In r4, `W = PACKET.parents[4]` resolves to the specificity-ladder worktree, and `CANDIDATE = W/'.superpowers/sdd/plan-a2-full-score-operational186/candidate'`; `TESTS` is that candidate's `tests` directory. The orchestrator's `root-dispatch/actual-path-expression-check.json` records that both directories and all three test files exist. There is no r4 candidate/test-path defect. The dependency-closure findings above are separate and unchanged.

This report is at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/242-a2-fixture-import-closure-handback.md`.
