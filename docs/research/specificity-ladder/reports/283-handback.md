# Hand-back 283: A3 isolated correction source review

Agent: independent source reviewer, gpt-6.1-sol. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task-4-correction282-brief.md`. Status: resolved for source-only corrected draft readiness.

## What changed

**Verdict: READY as a narrowly scoped corrected draft. No blocking spec or quality finding.** This does not authorize publication, launch, replacement of active artifacts or native acceptance. Root should retain its consolidated-terminal-outcome gate before freezing a replacement.

Only `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction-review283/review_checks.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction-review283/checks.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/283-handback.md` were written. No source, Git, RS, remote, scheduler or active evidence changed. No author narrative was read. Root may lint this handback centrally; worker RS commands were prohibited.

Spec review:

- The cost test now derives the counterfactual map through the original `_cost_packing_proofs([baseline])` and passes that map to the unchanged projector (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction282/tests/test_a3_prepared_pilot_target.py:720`). Original `_cost_packing_proofs` indexes by `(digest(full receipt), packing id)` and independently reads/authenticates the existing completed measurement reference (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py:3028`). The unchanged projector computes the same full-receipt digest before its typed proof lookup (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_workload.py:1249`). Zeroing startup/validation cost changes that key while retaining measurement evidence; reusing the measured map was therefore invalid. This correction rebuilds the lookup through existing validation. It neither publishes nor signs the in-memory counterfactual, creates a fake proof, nor changes cost mathematics.
- `resolved_object` now rejects absent/non-dictionary references and missing, empty or wrongly typed paths through `require` before reference I/O (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction282/component_analysis/a3_direction_runtime.py:2713`). Nonempty strings and `os.PathLike` paths remain admitted to the original byte-reference equality and `read_object` checks. Original references are dictionaries with canonical string paths (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py:50`); the new boundary follows that existing contract. Exact reference equality, object completeness and all subsequent source/authority/resource checks remain intact. There is no catch-all or widened expected exception.

Quality review: both two-file hashes match the supplied frozen draft pins. Independent AST comparison finds only the named runtime function and cost test changed. All 114 test assertions, every decorator/parametrization and all other top-level ASTs are unchanged. Direct diff inspection also shows the runtime change is confined to nested reference validation; subsequent authentication is untouched. No mismatch was found.

## How verified

Read original source and isolated diffs, actual JUnit failure traces, raw run manifest, root terminal check, the extracted probe implementation and machine pure-check results. The traces identify the projector lookup failure and leaked missing-reference `KeyError`, rather than a numeric/envelope failure.

```bash
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction-review283/review_checks.py
```

Observed exit zero. Both original and draft hashes matched; unchanged assertions/decorators/other top-level ASTs passed comparison. Extracted reference probes reproduced nine malformed-boundary failures on old source and zero on draft in both supported interpreters; two valid string/Path cases retained reference/read order, and two unequal references still rejected before payload read. These probes stub I/O and do not establish native acceptance. Independent evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction-review283/checks.json`.

Existing digest probe evidence in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction282/pure-check-results.json` also demonstrates different receipt digests and a missing counterfactual key with unchanged evidence. Source inspection establishes why the original proof-map constructor repairs this lookup; no application module was imported locally.

## Execution evidence

No new native run was executed. Existing failed-run evidence inspected:

- Job id and cluster: 50319105 on Bridges-2.
- Exit code/state: raw run manifest exit 1, normal completion false; root supplied terminal scheduler result FAILED 1:0. This was a failed run, not partial acceptance.
- Row counts: raw JUnit contains 112 cases, 110 passes, two failures, zero errors/skips. Exact failures are `test_prepared_costs_and_envelope_are_charged` and `test_prepared_migrated_intake_and_legacy_rejection[missing-preparation]`.
- Baseline reproduces: root terminal check records five observed expected failures against five required baseline cases, zero errors/skips, and normal oracle completion. This does not establish candidate success.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-r2-sharded/jobs/job-50319105/child/execution/run_manifest.json`, commit `538109e809285b6ddc45d42df8786270a65f7b12`; raw JUnit `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-r2-sharded/jobs/job-50319105/child/execution/junit.xml`; root terminal evidence `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-deployment273/mgnp-0/root-terminal-check.json`. Native interpreter recorded Python 3.12.13 / pytest 9.1.1. Root terminal evidence reports equal before/after source and passing final host source/allocation checks.

## What is NOT done

No full/native tests, native imports, genuine measurement, source publication, job submission or GPU work. No assertion is made that this draft passes either full native environment. Other shards and queued BASE outcomes remain root-owned and must be consolidated before a replacement freeze; their current state was not queried by this worker.

The changed whole runtime digest requires fresh source-dependent closure/authority later. Both-environment focused native validation, complete baseline/oracle reconciliation, genuine BASE equality, exact export/import closure, authentic prepared-target materialization and cold/warm resource measurements, original prefit numerical cases and aggregate/reconciliation, receiver feasibility, paired M1 cap, selection dependencies and all numerical/GPU admission gates remain open. Prior partial passes supply no permission to skip them.

## Open questions

None blocks retaining this draft for the consolidated correction. Default: root waits for all active terminal outcomes, incorporates any additional attributable failures coherently, then independently freezes and validates any replacement. No automatic retry or publication follows this verdict.
