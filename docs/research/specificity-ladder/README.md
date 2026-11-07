# Specificity ladder: session closed, research paused

Can a part of Llama-3.1-8B-Instruct be necessary for pressured deception while remaining dispensable when the user openly asks for the wrong answer, for honest behavior, and for unrelated tasks? This session built that comparison and tested existing component sets and newly trained masks. The user ended the session on November 7, 2026. A fresh session may continue the unfinished science from [RESUME.md](RESUME.md); the original requirements are in [START.md](START.md).

## A1: the tested component sets fail specificity

The transparent user-turn control retained enough examples at the original margin, so neither fallback was needed. The completed control-ladder experiment found that the tested fabrication and selective-emphasis component sets fail the registered specificity rule. They remove only 23.9% and 23.5% of the pressure effect, compared with 31.6% and 30.4% of the transparent-inversion effect. Honest behavior and the knowledge floors also suffer. The rule required at least 50% pressure-effect removal, less than 25% inversion-effect removal, and less than five percentage points of collateral accuracy movement.

The run contains all 28,884 expected rows and 3,396 positive controls. The answer-mover screen selected no candidates, so the full and mover-excluded groups coincide. Selective-disclosure results remain descriptive. This is a result about the tested sets under this assay, not proof that no deception-specific component exists. The readout is fixed-answer choice, not generated-text honesty or refusal. See [report 98](reports/98-full-a1-audit-handback.md).

## A2: matched masks fail the membership bars

All eighteen masks were trained: pressure and transparent-inversion masks for three tasks and three seeds per condition. The completed comparison fails the seed-stability and head-containment bars on every task. Every pairwise mixed-component Jaccard is below 0.5, and every pressure-mask head-containment ratio is below 0.9. The original masks and all nine pressure-minus-inversion sets are retained without selecting successful seeds.

This reviewed result was already available on November 2 and is now registered as local finding F3 and global finding F-lad-003. It is a membership result. Full functional specificity scoring of these masks remains unfinished; a timing/control pilot does not complete that test. See [report 139](reports/139-a2-comparison-freeze-handback.md).

## A3: no scientific result

The below-head direction, neuron-range and edge experiments have no scientific result. Harnesses, CPU comparisons, test packets and preparation artifacts exist, but they do not establish a successful below-head intervention or a scientific null. A3 used **0.65 of its 40 GPU-hours**: the ledger records 2,342 actual GPU-seconds and 1.5 reserved GPU-hours, including the retained cancelled reservation. CPU preparation time is separate.

The session ledger records 34.3668 GPU-hours reserved against the 125-hour total cap, 71,989 actual GPU-seconds (about 20.00 GPU-hours), and no paid API spend. Existing charges are preserved. [The ledger](ledger.json) remains the accounting record.

The closure preserves trained masks, original outputs, Bridges staging and logs, source commits, accepted packets and unfinished drafts. [The transfer records](wrapup/) document collection. [The restart guide](RESUME.md) separates the original scientific work from additional engineering gates that a fresh session may simplify or replace.
