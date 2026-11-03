# Last message of d2-reviewer ad2-reviewer-9e79f9a260243e09 (2026-11-02T22:41:29-05:00)

The D2 review is written and lint-clean, and the summary has gone to the team lead. The finding as stated is fair, but it needs qualifiers, and U1 should not be admitted on this result alone.

- **The rule was applied as frozen.** The 15-point bar, the interval rule, the refit-primary refusal control, the gate and the samples all match the spec. Every number in the brief reproduces. Changing the read-stage code after the job did not change any classifier number.
- **The SDR gap comes from one form of inversion clause.** The gap is 0.241 where the I clause has the predicate form. It is zero on SDR's act-form and other-form clauses, and on FAR, whose clauses are all act-form. Where I names the wrong answer as D does, the classifier cannot tell them apart. The classifier reads the clause wording, not whether the listener is deceived.
- **The I condition never tells the model the user is aware.** Its "transparency" is only drill, quiz or game framing, so D against I was never a clean test of listener knowledge.
- **The resume note misreads the ablation.** It says the D-against-H axis is "largely the refusal direction", but that does not hold. Removing the refusal direction shifts every condition toward "yes" and shrinks the D-H spread by only 16 to 37 percent. The refit classifier still separates D from H perfectly.
- **The SDR pass is fragile.** It rests on 40 misses where 37.5 are needed, and about 40 percent of cluster resamples fall below 15 points.
- **The first-token proxy cannot detect maintenance.** It has no maintenance tokens, so its agreement is just the share of corrected rows.
- **The judge labels hide some D refusals.** Second-turn refusals that only D produces sit inside the "unclear" label and vanish under ablation.
- **The freeze order does not affect the verdict.** The code ties the proxy tokens to calibration rows only. The 10:40 pm "clarification" should still be logged as a process deviation.
- **The ruling R6 iv cannot admit U1 yet.** Two of its three conditions are met, but the new ruling it requires has not been written. The result also does not fit U1's planned contrast, D against listener-visible D on FAR first. Before any U1 or patching work, the review asks for two controls: an honest-instructed H arm, and a D-I reading restricted to act-form ids.

Hand-back 07's Results section was complete when I read it. It agrees on every number but omits the clause-form breakdown, the D refusals and the margin counts.

I ran no git, so the lead should confirm that the judge hash was in the spec when the job ran:
```
git show fb2cb9e:docs/research/deception-divergence/spec.md | grep -c 1e41b6b92a0d0c92
```

A start-up hook asked me for a hand-back file. I did not write one, because the lead allowed only the review file, and I flagged this to them.

File: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reviews/04-d2-review.md`
