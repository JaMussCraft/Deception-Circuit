# Ticket 06: what the coarse v2 circuits are (stages 1 and 2 combined)

The six coarse heads-only circuits are evaluated with evals 1-4 on Bridges-2 H100s:

- D (deceptive) and H (Honest Twin) for far_v2, sdr_v2 and ser_v2;
- 2 drift-control cells, 24 cells in stage 1, and 39 in stage 2.

The method is interchange ablation, 1,000 test items per cell, 20 size-matched random circuits per null,
and leaf composition, with no EVAL 5. The numbers are in `06-stage1-results.md` and `06-stage2-results.md`,
with `.json` beside each. The drift control is in `06-handback.md`. The cross-GPU drift against Delta A40s
is about 1e-3 on rates.

## Verdict in plain language

**The circuits are mostly shared answer machinery, not mechanism-specific deception circuits.**

Each D circuit (55-60 heads) is faithful: alone it reproduces 90-96% of the deceptive answers its task
was pruned for. Removing its heads removes the deception completely, on its own task and on both other
tasks.

But the same removal also flips the model's honest answers, given without pressure or under an honest
instruction, to the other item. So these heads carry which item the model names, whatever the reason.
A 31-head core common to all three D circuits does this alone, at the lowest collateral cost. The Honest
Twin circuits contain the same core: knocking out H removes deception just as well.

**Mechanism-specific heads exist, but they are small and partial.** The heads unique to one task's D (8
far, 14 sdr, 10 ser) are the only sets whose removal lowers deception without broadly flipping honest
answers:

| task | deceptive answers removed | honest no-pressure answers flipped | separation from random |
| --- | --- | --- | --- |
| far | 29% | none | 0/4 (5th percentile) |
| sdr | 24% | 21% | 4/4 |
| ser | 48% | 34% | 4/4 |

The heads D has and its Honest Twin lacks (D-H) behave similarly, most cleanly on far. There they remove
81% of far's deception and flip only 18% of honest answers. Neither D-H set is task-specific across tasks.

**Pressure contingency is incomplete.** Without the pressure clause, the D circuits alone still name the
deceptive item on 20-53% of rows (far the most). They also give the honest answer on 44-78% of the
no-pressure test set.

## Per task

| | far_v2 | sdr_v2 | ser_v2 |
| --- | --- | --- | --- |
| D alone (acc / KL) | 0.964 / 0.10 | 0.924 / 0.14 | 0.900 / 0.15 |
| D knockout, home (acc, sep) | 0.000 (3/4) | 0.000 (4/4) | 0.001 (2/4) |
| D knockout, no-pressure answers inverted | 99% | 99% | 100% |
| D&H knockout (heads) | 0.001 (32) | 0.000 (39) | 0.000 (36) |
| D-H knockout, home (heads, sep, inverted) | 0.191 (26, 4/4, 18%) | 0.513 (21, 1/4, 28%) | 0.228 (19, 4/4, 76%) |
| H-D knockout on D's test set | 0.491 (0/4) | 0.656 (4/4) | 0.341 (4/4) |
| exclusive D_t - D_u - D_v knockout | 0.694 (8 heads, 0/4, 0%) | 0.750 (14, 4/4, 21%) | 0.496 (10, 4/4, 34%) |
| H alone on D's test set | 0.219 | 0.905 | 0.813 |
| H knockout on D's test set | 0.000 | 0.000 | 0.000 |
| D alone, no pressure (deceptive item) | 0.534 | 0.198 | 0.278 |

- **far.** This is the most mechanism-like task. Its H does not deceive alone, its D-H is
  deception-leaning, and its 8 exclusive heads flip some deceptive answers with no honest-answer
  inversion. But its D alone is the least pressure-contingent (53% deceptive without pressure).
- **sdr.** Almost everything is shared. H alone deceives (0.905), and D-H is weak at home. Its 14 exclusive
  heads are a small, separated effect (24%).
- **ser.** This lies between the two. Its exclusives have the largest specific effect (48%, 4/4). H alone
  deceives (0.813), and D-H acts like answer machinery.

## What this means for the next steps (for the researcher)

1. **Gates.** The coarse heads-only circuits pass the necessity and faithfulness reading that the v1
   coarse SDR wave used. They do not pass a specificity reading. The no-pressure and honest-instruction
   inversion rows are the specificity test that matters here, and every full-circuit, core and H knockout
   fails it.
2. **Candidates for mechanism-specific analysis.**
   - The exclusive heads: sdr and ser are separated; far is not, but it never inverts honest answers.
   - far's D-H heads.

   These are the sets component analysis or path patching would target. Ticket 06 ran no component
   analysis. `component_analysis/dataloaders.py` would need its v2 extension first (recon A3).
3. **Interchange caveat.** Every knockout reading here comes from interchange ablation. An answer-carrying
   head shows up as an inversion, not as removal. A mean-ablation or zero-ablation replication of the core
   and exclusive cells would separate "carries the answer" from "makes the answer deceptive" more directly.
   That would be about 1-2 H100 GPU-h and is not run.
4. **Budget.** Ticket 06 used 11.0 of its 20 Bridges-2 H100 GPU-h reconciled, 7.39 actual. No Delta GPU
   was used.
