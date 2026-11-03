# Last message of d2-worker ad2-worker-f58bfa5283c22b81 (2026-11-02T23:04:09-05:00)

The pre-registered D2 follow-up plan is written and lints clean. As briefed it needs 3,927 new rows, about 0.37 GPU-hours on one Bridges-2 H100, with no generation, no judge and no paid calls. No code, job or git command ran.

**Design.** The plan adds two conditions on the D2 ids that already exist, so the D, I and H features are reused unchanged.
- **Honest-instructed H.** It keeps the same forced wrong answer under an honest instruction. That instruction mirrors D's clause in wording, length and form.
- **D with a true answer.** It keeps D's instruction but forces the true item as the first answer.

**Honest clauses.** No existing pool fit, because the matched-honest pools were written for the older v1 clauses. I wrote one honest mirror for each of the 50 v2 D clauses, mostly by swapping a single word such as "wrong" for "correct". 34 of the 50 pairs differ by exactly one word. A scratch check outside the repo covered all 1,909 rows the honest condition needs: every row fits the existing builder's alignment test with zero token difference, and no form is excluded.

**Branches.**
- **(a)** The new classifier cannot tell D from honest-instructed H on any task. U1 is closed.
- **(c)** On FAR (210 ids) or SDR (35 ids), the D-I gap among clauses that name the wrong answer reaches 15 points, the interval excludes zero, and refusal does not explain it. U1 may be re-admitted.
- **(b)** Everything else. U1 is closed.

SER has a single such id, so it is excluded from that reading.

**Cost.** The briefed design needs 3,927 rows and the four-arm version 4,636. At the D2 job's measured rates that is 0.37 and 0.41 GPU-hours, with a 40-minute reservation. The D2 plan's own model constant puts both designs over the 0.5-hour cap, at 0.52 and 0.59 hours. That constant overestimated the real D2 job by about 1.5 times.

**Decisions for the lead before writing ruling R15.**
- **A fourth arm.** It pairs the honest instruction with a true answer. D obeys its instruction while the two new arms both disobey theirs, so without it a model reading "obeyed or not" looks the same as "has lied". It costs 709 rows. This changes the lead's rule for the true-answer reading.
- **The pick rule.** Each row gets the mirror of its own D clause, not a random draw from the builder's pool. The draw stays as a fallback and was never needed.
- **Hand review.** Twelve borderline honest clauses need a reading before the pool is frozen.

The plan is at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/plans/D2-followup-plan.md`.
