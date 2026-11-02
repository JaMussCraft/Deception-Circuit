# Specificity ladder: research in progress

Can a model component be necessary for pressured deception while remaining dispensable for a transparent request to give the wrong answer, honest tasks and unrelated tasks? The approved [starting prompt](START.md) tests this through a control ladder, matched mask training and below-head interventions. The overall direction remains active; [RESUME.md](RESUME.md) has current execution state and [WORKLOG.md](WORKLOG.md) records decisions and findings.

## Audited control-ladder result

The control-ladder phase is complete. The tested fabrication and selective-emphasis deciding sets fail the registered specificity rule. This is reviewed finding F2, supported by the [independent full-run audit](reports/98-full-a1-audit-handback.md) and its [calculations](reports/98-full-a1-audit.json).

The table reports derived percentages from the [audit calculations](reports/98-full-a1-audit.json). D is pressured responding; I is transparent user-requested inversion. Target choice is a full-vocabulary fixed-answer argmax, not a generated-text honesty or refusal judgment.

| Tested set | D target choice, intact → patched | D pressure effect removed | I effect removed |
| --- | --- | --- | --- |
| Fabrication | 100% → 53% | 23.9% | 31.6% |
| Selective emphasis | 100% → 80% | 23.5% | 30.4% |

The frozen rule requires at least half of the D pressure effect removed, under a quarter of the I effect removed, and less than five percentage points of collateral accuracy movement. Both sets also fail honest preservation and both knowledge floors. Their paired pressure-cluster intervals remain on the failing side of the D and I thresholds; the audit retains the small-cluster precision caveat. Selective-disclosure results remain descriptive because of the original set's qualification. See the [audit](reports/98-full-a1-audit-handback.md) for all estimates, intervals, crossed controls and utility results.

The full run contains 28,884 of 28,884 expected rows and 3,396 of 3,396 positive controls. All recorded replay and full-vocabulary donor-recovery errors are zero. Frozen execution source: `5f450dc93dac707af649dee8c8ca60888b2831db`. These execution claims are documented in the [audit calculations](reports/98-full-a1-audit.json) and the audit's complete evidence block.

The answer-mover screen selected no candidates, so the full and mover-excluded groups coincide. This does not show that answer machinery is absent. The result concerns these tested sets in one frozen assay; it is not a distinct-seed replication or a proof about every possible deception circuit.

## Remaining research

Matched pressure/transparent-inversion mask training and analysis remain in progress. Direction, exact receiver-clamp edge and constrained-mask runtimes are being integrated and reviewed. No below-head scientific result is established yet. These phases continue under the original [specification](spec.md), with measured cost admission and unchanged assessment membership, thresholds and budgets. Neuron expansion remains conditional on the registered direction result.
