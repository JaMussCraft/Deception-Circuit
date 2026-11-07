# Hand-back 282: Two-file validation correction draft

Agent: Sol. Status: resolved isolated drafting; native acceptance outstanding.

## What changed

Only isolated copies and supporting probes/evidence were added under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction282`:

- `component_analysis/a3_direction_runtime.py`: explicit missing/malformed reference and path rejection before existing equality/read in `_completed_pilot_source.resolved_object`.
- `tests/test_a3_prepared_pilot_target.py`: obtain the zero-cost counterfactual's own proof map through `_cost_packing_proofs([baseline])`, retaining all original assertions and native proof validation.
- `pure_probe.py`, `check_scope.py`, `pure-check-results.json`, `scope-pins.json`, and two exact `.diff` files preserve the bounded checks and review boundary.

Detailed implementation/scope report: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task-4-correction282-report.md`.

Active runtime, original test, exercised suite and prior packets were not edited. One authorized wording correction in report 281 identifies the jobs as Bridges jobs observed from Delta; its saved observations are untouched.

## How verified

Before implementation, the extracted reference-boundary probe failed against the pinned original source with exit one. After implementation, the identical specimens passed against the isolated draft with exit zero. Controlled boundary stubs preserve the byte-equality/read behavior but are not native artifact authentication.

Commands executed with each of `/sw/external/python/anaconda3/bin/python3.9` and `/u/swong2/.conda/envs/mgnp/bin/python` as `PYTHON`, with full script paths recorded in `pure-check-results.json`:

```bash
PYTHON /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction282/pure_probe.py red
```

Observed: exit one, nine malformed boundary specimens expose the original missing shape guard. Valid string/Path and conflicting-byte-reference controls pass.

```bash
PYTHON /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction282/pure_probe.py green
```

Observed: exit zero, nine malformed specimens reject before reference I/O; two valid path shapes retain equality/read, two conflicting references reject.

```bash
PYTHON /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-failure281/diagnosis/digest_probe.py
```

Observed: exit zero, unchanged evidence plus changed timing fields changes the receipt digest and makes the old table key miss. Scope is synthetic digest/dictionary behavior only, never proof minting or native cost acceptance.

```bash
PYTHON /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction282/check_scope.py
```

Observed: exit zero. Only the two intended top-level functions differ; all other top-level ASTs and all 114 assertion ASTs remain equal. Every outer completed-source statement except the nested helper is equal; original helper byte-equality and read/return nodes remain equal. Both complete copies compile in memory on both interpreters. Original input hashes still match the brief.

Draft runtime SHA-256 is `1d6c3886a7634641a8a4ad64135adeef34dcdac7ce6b388e8441df1bf2cea116`; draft suite SHA-256 is `2f89de3edb0ac5d513b98c018c6ab1393179b73d9ee67c64d725a064eaa09fb3`. Exact inputs, diffs and outputs are in the isolated evidence directory.

## Execution evidence

- Local checks: eight bounded non-native subprocess checks across two interpreters; all expected exit statuses matched, stderr empty. Two original-boundary checks exit one as intended; six checks exit zero.
- Native RED source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-failure281/observed-phases-02.json` preserves the two actual failed call phases from Bridges job 50319105, observed from Delta. This agent did not query or run that job.
- Native GREEN: not yet verified; no new native run, suite completion, row count, baseline comparison or `run_manifest.json` is claimed. These remain root-owned gates.
- Pure evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction282/pure-check-results.json`; static/source evidence is adjacent `scope-pins.json`. No new commit was produced.

## What is NOT done

No publication or successor packet freeze, native imports/tests, full target construction, jobs, scheduler/SSH/Git/RS commands, agents, authority rewrites, altered controls, reduced case counts or automatic reruns. Root owns independent review, lint/number checks, terminal outcome consolidation and any later native attempt. The unchanged complete case set across both environments and final source/resource/numerical/GPU gates remain.

## Open questions

- Do both existing jobs expose additional attributable failures before terminal completion? Default: root consolidates the full outcomes before freezing a replacement.
- Does independent full-diff review accept these two isolated changes? Default: retain the draft without publication until reviewed.
- Do later complete native checks pass with the unchanged assertions and controls? Default: no acceptance claim from pure probes or static scope checks.
