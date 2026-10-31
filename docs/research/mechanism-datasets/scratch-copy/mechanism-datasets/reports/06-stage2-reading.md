## Reading (impl-06)

The conventions are as in stage 1:

- Under interchange ablation, a knockout of answer-carrying heads makes the model name the other item.
- The no_pressure and honest_instruction rows, where the full model is honest at about 0, show whether a
  knockout is deception-specific or inverts every answer.
- On `<t>_v2_nopressure`, accuracy counts the honest item.

**Cross-task transfer.** Removing any task's D heads removes the deceptive answer on every task:
accuracy 0.000-0.005 across all nine D x test-set cells, with 995-1000 of 1000 flipped. It also inverts the
no-pressure answers (0.99-1.00).

No D circuit is task-specific in necessity. The circuits alone transfer unevenly:

| D circuit alone | far | sdr | ser |
| --- | --- | --- | --- |
| D_sdr | 0.87 | 0.92 (home) | 0.77 |
| D_far | home | 0.80 | 0.59 |
| D_ser | 0.32, KL 1.35 | 0.88 | home |

**Shared D core (31 heads, in all three D circuits).** Its knockout removes deception on all three tasks:

- accuracy 0.000-0.003, 4/4 separated against random 31-head sets (null mean 0.71-0.79);
- the lowest collateral of any full-effect knockout: wikitext KL/token 0.076 vs a null of 0.124;
- but it inverts the no-pressure answers (0.995).

The core alone is not sufficient: deceptive accuracy is 0.17-0.29 and KL 1.1-1.5. Its high no-pressure
"accuracy" (0.80-0.95) is the interchange artifact. The non-core heads carry the swapped item, so the
circuit names the other item; it is not producing deception. The core is shared answer-selection
machinery.

**Mechanism-specific heads (exclusives, the --xor family).** The heads one task's D has and the other two
lack (8 far, 14 sdr, 10 ser) are the only sets whose knockout reduces deception without broadly inverting
honest answers. Their effect is partial.

| exclusive | flipped of 1000 | KO acc vs null mean | separation | no-pressure inverted | wikitext KL/token |
| --- | --- | --- | --- | --- | --- |
| far (8 heads) | 294 | 0.694 vs 0.927 | 0/4 (5th percentile; one random set reached 0.436) | 0% | 0.04-0.05 |
| sdr (14 heads) | 244 | 0.750 vs 0.980 | 4/4 (z -5.5) | 21% | 0.04-0.05 |
| ser (10 heads) | 484 | 0.496 vs 0.967 | 4/4 (z -6.7) | 34% | 0.04-0.05 |

**H on D's test set.**

- **H alone.** It produces the deceptive answer on sdr (0.905) and ser (0.813), but not on far (0.219,
  KL 2.2).
- **H knockout.** It removes deception on every task (0.000, all 1000 flipped) and inverts the no-pressure
  answers, exactly like D's.

So the Honest-Twin circuits share the answer machinery. On sdr and ser they also contain enough of D's to
deceive. The "H does not remove deception" control fails because the shared core is in both.

**D on the nopressure test set.**

- D alone gives the honest answer on 0.44 (far), 0.78 (sdr) and 0.70 (ser) of rows.
- D's knockout removes the honest answer (0.000-0.004).

D's heads are needed to answer at all, whether or not pressure is present.

**D-H across tasks (conditional, all 6).** The off-home D-H knockouts reduce deception by 37-69%, and
four of the six separate on 3 or 4 of 4 metrics. How much they invert the
no-pressure answers varies:

- sdr's D-H is the cleanest off home: on far it reaches 0.399 (4/4) and inverts only 20%, better than at
  home (0.513, 1/4).
- far's D-H reaches 0.361 on sdr (3/4, 41% inverted) and 0.631 on ser (0/4).
- ser's D-H reaches 0.339 on far (4/4) and 0.315 on sdr (4/4), but inverts 97% and 68% of the no-pressure
  answers.

There is no task-specific D-H effect. Where D-H works off its home task, it works through answer-leaning
heads.
