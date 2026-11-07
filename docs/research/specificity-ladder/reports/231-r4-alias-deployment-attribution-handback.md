# Bridges deployment alias-test attribution

Status: handed-back

## What changed

No source correction is required for the observed host-only inventory assertion. Correct literal aliases must remain under `/projects/beto/swong2/Alignment`. The test derives its expected worktree from physical `__file__` when run on the Bridges host and therefore expects `/ocean/...` at line54. In the intended virtual container namespace, the unchanged test expects the correct `/projects/...` targets.

## How verified

Read raw deployment234 `host-container-dry-run.json` and exact test lines47–56. The script passes actual bound-config and image checks before executing unittest. Nine of ten actual-host cases pass; the sole assertion failure is the literal target prefix comparison above. The inventory name-set assertion precedes that failing comparison. The script exits at this failure, so its later container commands did not execute. Review evidence is in `.superpowers/sdd/plan/a3-green-bridges-review231/r4/attribution.json`.

Nine actual-host compatibility cases plus the same unchanged inventory case passing in the intended virtual container can close those scoped gates, provided exact config/source hashes and all eight aliases remain bound. This preserves every assertion and tests it in its applicable namespace. It must be reported as split evidence, never as ten host passes. No minimal test-only expectation patch is necessary to proceed with that bounded attribution.

## Execution evidence

Observed raw host wrapper exit1: ten unittest cases, nine pass, one namespace-specific assertion failure. No tests or remote actions were executed by this reviewer. Same-case container success is not yet observed in the reviewed receipt.

## What is NOT done

No overall deployment/test/source acceptance, actual container-case pass, observer dry-run, effective mount check or scheduler/model admission. The failed host receipt remains valid preserved evidence. No code edits, git, RS, jobs, remote calls or agents.

## Open questions

Root should run the unchanged inventory case in the correct virtual namespace and the separately planned observer/container checks. If those pass with exact binding, retain this scoped attribution without changing correct production aliases or starting another source revision. Root owns report lint.
