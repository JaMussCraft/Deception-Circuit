## Reading (impl-06)

**How to read a knockout here.** Accuracy counts the deceptive item. The knockout is an interchange
ablation: the removed heads take their activations from the item-swapped prompt. A knockout of heads that
carry the answer itself therefore makes the model name the other item, whatever the prompt.

The pressure-variant rows tell the two cases apart:

- **Deception-specific heads.** On no_pressure and honest_instruction prompts the full model already gives
  the honest item, at accuracy about 0. Removing deception-specific heads should leave those rows near 0.
- **Answer-carrying heads.** Removing them inverts those rows towards 1.

| circuit | knockout accuracy, D's test set | knockout accuracy, no_pressure |
| --- | --- | --- |
| D, all three tasks | 0.000-0.001 | 0.994-1.000 |
| D&H, all three tasks | 0.000-0.001 | 0.995-1.000 |
| far D-H | 0.191 | 0.182 |

The full D and D&H knockouts flip 998-1000 of 1000 deceptive answers to honest. They also turn the honest
no-pressure answers deceptive. So most of D's head set, and all of the shared core D&H, carries the item
choice. The heads are not specific to deception.

The KO answer is always the honest item on D's test set (`distractor_frac` 1.0). That is an item inversion,
not a positional default.

**Separation counts.** Every D, H and D&H knockout sits at the 0th percentile of its 20 random-KO head sets
on all four metrics. A count below 4/4, for example D_far 3/4 or D_ser 2/4, comes only from the z <= -2
rule. Its random-KO null has a large spread (accuracy std about 0.26-0.32). The wikitext collateral of every D
knockout is at or below its random-KO median: KL/token 0.20 / 0.28 / 0.22. That is under the 0.28 gate EVAL
5 later used.

**Sanity (eval 1).** It reproduces in-run node_eval exactly for far D and within 1e-4 for ser D. Both were
trained on H200s.

Three cells flag the 0.002 / 0.01 tolerances, by 1-3 items of 1000 or a logit diff of +0.011 to +0.018:

- far H;
- sdr D;
- ser H.

This is the cross-GPU bf16 drift seen before (A40 to A100 in the coarse SDR seed wave). It is not a mask
or reload error.

**Sufficiency.** All six circuits alone reproduce their own test set:

- accuracy 0.90-0.98 and KL 0.09-0.20;
- every size-matched random circuit is at accuracy 0, beaten on 4/4 metrics.

Without the pressure clause, the D circuits alone still name the deceptive item part of the time, while
the full model gives the honest item:

| D circuit alone | no_pressure accuracy |
| --- | --- |
| far | 0.53 |
| sdr | 0.20 |
| ser | 0.28 |

So the D circuits are not fully pressure-contingent on their own, and far least of all. The D&H core alone
keeps 0.24-0.58 of the deceptive behaviour.

### Per task

- **far_v2.** The far result is the cleanest.
  - D's heads are necessary: KO 0.000, all 1000 flipped. They are not deception-specific, because the
    knockout also inverts the honest answers.
  - The D-only heads (D-H, 26 heads) are the deception-leaning part. Their knockout brings deception from
    1.0 to 0.191, which is 81% of D's effect, 4/4 against random. It inverts only 18% of the no-pressure
    answers.
  - The H-only heads (H-D, 28) do no more than random: 0.491 vs a null mean of 0.818, 0/4 separated.
  - D&H (32 heads) is shared answer machinery.
- **sdr_v2.** There is no clear deception-specific part.
  - D's heads are necessary (0.000, 4/4), and D&H (39) carries the whole effect (0.000).
  - D-H (21 heads) is weak: 0.513 vs a null mean of 0.870, 1/4, 49% of D's effect.
  - H-D (19 heads) is comparable: 0.656, 4/4 against its higher null of 0.930.
  - The D/H difference does not isolate deception on this task.
- **ser_v2.** There is a partial, mixed D-specific part.
  - D's heads are necessary (0.001), and D&H (36) carries the full effect.
  - D-H (19 heads) gives 0.228, 4/4, 77% of D's effect. But it also inverts 76% of the no-pressure answers,
    so it still mostly carries answer choice.
  - H-D (33 heads) gives 0.341, 4/4.
  - Both exclusive parts matter, and neither is deception-specific.
- **H circuits (own honest test sets).** H's knockouts remove the honest answer (0.000-0.002) and invert the
  no-pressure rows (1.0 to 0.0). They are the same kind of answer machinery.

  Whether H "does not" remove deception is the stage-2 control (H on D's test set). Stage 1 shows only that
  H's exclusive heads (H-D) do no more than random on far, and do on sdr and ser.

### Conditional stage-2 cells (D-H cross-task KO)

By the pre-stated rule (4/4 KO-null separation on the home task), D-H is strong on far and ser and not on
sdr.

The recommendation is to run the conditional cells for **D_far - H_far** and **D_ser - H_ser** on the other
two tasks' D test sets. That is 4 of the 6 cells.

- far's D-H is the most interesting: the only deception-leaning knockout in stage 1.
- ser's passes the rule but behaves like answer machinery.
- If the user prefers the symmetric grid, the two sdr D-H cells cost about 0.2 H100 GPU-h more.
  `--include-conditional` currently adds all 6. Running only the 4 needs a small selector in
  `gen_cells.py`, about 10 lines, which I would add on the go.
