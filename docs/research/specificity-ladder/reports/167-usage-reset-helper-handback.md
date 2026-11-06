# Hand-back 167: usage reset helper checkpoint

Agent: Terra worker. Status: blocked on HOLD at the carried usage checkpoint; r5 is incomplete and unaccepted.

## What changed

Created `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/root-model-phase-release-helper/r5` as a copy of r4's files, plus the approved `test-matrix.json`, `test_usage_reset.py` and `red-base.log`. No production implementation change has been made; r5 manifest still describes r4 and must be replaced after implementation. r4 was not edited.

## How verified

In r5, ran:

```bash
PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m unittest -v test_usage_reset > red-base.log 2>&1
```

Observed `Ran 1 test in 0.033s`, `FAILED (errors=7)`. The matrix exercises all cases as subtests; the errors include rejection of the intended new route and absence of route telemetry in the predecessor. Raw output is preserved in r5. This is RED only, not acceptance.

## Execution evidence

Not applicable: no runs.

## What is NOT done

HOLD arrived immediately after the RED atomic step. No implementation, GREEN, mgnp RED, complete suite, new manifest/ruling, independent review, real release, scheduler action, git or RS/private-state write was performed. The copied tests are incomplete pending approved design implementation. No r5 operational use is authorized.

## Open questions

After root explicitly releases HOLD, first inspect the complete `red-base.log`; then implement only `validate_usage` against the accepted design and run the same matrix on both interpreters plus all existing helper/cache tests, collecting raw logs. Add focused adversarial/integration cases as specified, preserve r4 and produce an r5 manifest/ruling and independent review. Root's checkpoint decision controls resumption.
