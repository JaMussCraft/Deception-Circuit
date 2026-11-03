# Last message of followup-reviewer afollowup-reviewer-713735aea6681c26 (2026-11-03T01:08:32-05:00)

The "(b) on every task" label is fair under R15. R15 was applied exactly as frozen, and I found no error in the code or the numbers.

1. **R15 as frozen.** The labels, signed rule, 0.30 spread, leave-one-cluster-out, refusal validity on the act-form ids and the interaction coding all match. All nine manifests are pre-registered on the pinned stack and direction, with zero fallback firings and 5,481 rows. The D2 hashes were checked first, and re-running the read reproduces the stored results to the last bit; the 43 tests pass.
2. **FAR's rate readout is saturated.** D's mean C_HI logit is 8.01 and I's is 5.66, against a threshold of 0. Only 2 of 210 I rows fall below it, so the null is a null of the rate readout, not of score space.
3. **FAR has a descriptive score gap.** D minus I is 2.35 logits [0.92, 4.34], about 15% of the D-to-HI span. Review 04 had already seen this under the old classifier (AUROC 0.711).
4. **That gap reads as wording, not listener knowledge.** Which I clause a row carries explains 91% of I's score. The gap tracks how many words the D and I clauses share. It falls to 1.19 [-0.20, 3.08] where D uses the same lie word as I. SDR shows no gap: 1.06 [-0.98, 3.02].
5. **The FAR interaction of 3.85 is partly inflated.** The honest version of I's clause scores 1.5 logits more D-like than D's honest mirror, which adds to the result. So it is no evidence of a signal beyond wording.
6. **Labelling and the joint reading.** The joint table's p values are positions on the HI-to-D axis, while R15 uses the same names for rates. "Instruction content" follows correctly everywhere. On SDR and SER, score space also shows a compliance-like component.
7. **SDR's 0.000 lower bound is structural.** Its (b) rests on 0.114 alone and is underpowered, with an upper bound of 0.25. FAR's upper bound of 0.028 is tight.
8. **One wording fix for the finding.** "Clause-driven on every task" overreaches, because SER has no form-matched reading.
9. **No new pre-registration on the existing clauses.** Only a new pool where I is D's own clause plus a transparency frame would isolate a listener signal, and that needs a new ruling.

Files are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/`:
- reviews/06-d2-followup-review.md
- reports/11-handback.md
