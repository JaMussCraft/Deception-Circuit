# Staged formal grader freeze command hand-back

Agent: registry implementation worker. Status: handed-back.

## What changed

The isolated staging root is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/grader-registry/`.

The staged source and tests preserve the canonical import layout:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/grader-registry/tree/projects/beto/swong2/Alignment/.agents/research_session/registry.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/grader-registry/tree/projects/beto/swong2/Alignment/.agents/tests/test_research_session_registry.py`

The minimal unified diff is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/tools/rs-freeze-grader.patch`.
The preimage manifest is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/grader-registry/preimage-sha256.json`.
The guarded operation list is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/grader-registry/ops/36-grader-registry.json`.
Test summaries are `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/grader-registry/test-results.json`.

Only registry.py gains production behavior: a handler and parser for `freeze-grader SLUG SHA256 --session ID [--root ROOT]`. Strict full matching rejects hashes with uppercase, whitespace, newline, wrong length or nonhex characters. The explicit selector must be nonempty and resolves through the existing session resolver; no impersonation option exists. The callback requires claimed or active status and exact ownership. It accepts an initial null or absent hash and an identical retry, and refuses replacement. The existing locked edit helper retains responsibility for loading, validation, date stamps and atomic writing. It changes no other row fields itself.

The copied package, helper modules, fixture files and tests support isolated test execution. cli.py, state.py and records.py are byte-identical to their canonical sources. Both canonical files named by the manifest remained byte-identical through final checks. No live registry or private session writer ran.

## How verified

All test commands used the following environment and isolated staged paths:

```bash
S=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/grader-registry
A=$S/tree/projects/beto/swong2/Alignment/.agents
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
```

The new tests were written and run before implementation:

```bash
/sw/external/python/anaconda3/bin/python3.9 -B -m pytest -q -p no:cacheprovider "$A/tests/test_research_session_registry.py" -k freeze_grader --tb=no
```

Observed expected red phase: `5 failed, 17 deselected`; the command was absent from the parser. A parser-exit assertion was corrected before implementation because CLI argument errors raise SystemExit rather than returning a status.

```bash
/sw/external/python/anaconda3/bin/python3.9 -B -m pytest -q -p no:cacheprovider "$A/tests/test_research_session_registry.py"
/u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -q -p no:cacheprovider "$A/tests/test_research_session_registry.py"
```

Observed: base `22 passed in 5.36s`; mgnp `22 passed, 18 subtests passed in 9.01s`; both exited successfully.

```bash
/sw/external/python/anaconda3/bin/python3.9 -B -m pytest -q -p no:cacheprovider "$A"/tests/test_research_session_*.py
/u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -q -p no:cacheprovider "$A"/tests/test_research_session_*.py
```

Observed: base `265 passed in 30.91s`; mgnp `265 passed, 50 subtests passed in 36.64s`; both exited successfully. No failures or skips appeared.

The new tests exercise initial freeze, active ownership, identical retry, full ID/tag/unique-prefix resolution, a newer foreign session sharing the cwd, invalid hashes, missing/empty/whitespace/unknown/ambiguous selectors, rejected impersonation option, foreign/unclaimed/paused/done/abandoned directions, conflicting freezes, unknown slug and invalid registry. Refusals compare original registry bytes. Successful calls compare every preexisting other fixture file, including private session, usage, direction state, worklog and ledger files. A wrapper around the real edit helper inserts another writer's completed summary changes before lock/load, then asserts those fields and unrelated rows survive. This is deterministic interleaving coverage, not a simultaneous-process stress test.

```bash
PYTHONPATH="$A" /sw/external/python/anaconda3/bin/python3.9 -B -c 'from research_session import registry,cli,state,records; print(*(m.__file__ for m in (registry,cli,state,records)), sep="\n")'
```

An equivalent Python check inserted the same staged parent and asserted that every resolved module path was beneath it. Observed paths all pointed to the staged package. No bytecode files were created in staging.

```bash
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging "$S" --wave A --only 36 --dry-run
```

Observed `2 op(s) selected from 2`, with registry `WOULD APPLY: +37 -0 lines` and tests `WOULD APPLY: +101 -0 lines`. Each operation requires its canonical preimage SHA to match. The tool was never run in application mode.

```bash
/u/swong2/.local/bin/codex-usage --pause-at 80
```

Observed `weekly.used_percent: 12`, `weekly.remaining_percent: 88`, `should_pause: false`, reset `2026-11-06T16:07:41+00:00`. The temporary session cadence was not changed.

## Execution evidence

Not applicable to scientific runs: this task ran isolated CPU unit tests and an application dry run. No Slurm job, cluster run, dataset rows, model baseline or scientific provenance manifest exists. Test commands and observed exit statuses are above; the staged summary is a test receipt, not scientific execution evidence.

## What is NOT done

No installation, live directions edit, actual grader freeze, grader hash recomputation, spec change, protocol documentation edit, usage/cadence/acknowledgement/gate change, GPU/API work, notebook execution, git command or subagent spawn occurred. The startup synchronizer was not run because live agent sources are explicitly outside this worker's write scope; startup remains the parent session's responsibility.

The minimal patch changes only the original source and test file identified in report thirty-five. Application and any live-source tests belong to the orchestrator after review. The broader suite run was the complete copied research-session suite, not the unrelated Deception-Circuit model tests.

## Open questions

The orchestrator should review and apply the guarded operation list through the approved tool. It must recompute the actual reviewed grader fingerprint and use the explicit owning session and primary research root before any benchmark. Initial grader metadata does not authorize benchmark spending or close other scientific preflight conditions. No human decision is required for staging.
