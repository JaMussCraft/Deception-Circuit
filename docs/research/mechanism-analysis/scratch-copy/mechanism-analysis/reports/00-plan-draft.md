# Mechanism analysis: plan on one page (for the user, 2026-10-25)

**Where we are.** The six coarse v2 circuits are faithful and necessary. They are mostly shared answer machinery:
a 31-head core sits in all three deceptive circuits. Small mechanism-specific sets exist: 8 heads for FAR, 14 for
SDR, 10 for SER. Every reading so far uses interchange ablation, which cannot tell "carries the answer" from "makes
the answer deceptive".

**The two possible headlines, fixed before anything runs.**

- **A.** A small set of **pressure mediators** sits on top of shared answer selection, and FAR, SDR and SER differ in
  where the pressure enters.
- **B.** No set of 20 or fewer Components mediates the pressure; its effect is spread over shared answer machinery.

**The deciding test.** Rank every head and MLP by how much the deceptive answer weakens when that Component's output
after the Pressure Clause is swapped for its value on the Neutral-Clause Twin (the same prompt with the clause
replaced by a neutral sentence). Build candidate sets of the top k, and also a greedy set. Then test them on a
**separate held-out sample**:

- **A** holds if swapping some set of 20 or fewer removes at least 75% of the deception, beats all 20 random
  layer-matched sets of the same size, and leaves honest answers almost unchanged.
- **A′** holds if the set removes the deception but also carries the answer. Path patching then decides whether the
  pressure enters at the set's queries, at the clause itself, or upstream.
- **B** holds if no set of 20 or fewer removes the deception.

A transparent **instructed-inversion control** ("name the result that is NOT failing", asked openly) checks whether
the mediators are about deception or about following an inversion rule. The paper says "deception" only if they
are not equally needed for open inversion.

## Phases (Bridges-2 H100 GPU-hours, reserved / expected)

| phase | what | GPU-h |
| --- | --- | --- |
| 0 | Code: v2 support, the neutral-twin pairing, the inversion control, Bridges-2 smoke and drift check | 2 / 1 |
| 1 | Mean/zero knockouts (36 cells), whole-model sweeps, the A-or-B test with its null | 19.5 / 12.1 |
| 2 | Component cells on all 123 circuit heads, 4 test sets x 3 tasks, roles | 3.5 / 2 |
| 3 | Path patching on about 60-80 candidate Components per task | 9.25 / 5.3 |
| 4 | Claims table, figures, limitations (CPU) | 0 |
| holdback | reruns, plus about 14 h freed when reservations reconcile | 0.75 |
| total | | **35 (70 SU) / about 20** |

Seeds, only if a headline rests on the identities of the mechanism-specific heads: 6 Delta GPU-h.

## How I proceed

**Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if
the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user is
always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.

Bridges-2 may go offline around Nov 9, so GPU work is planned to finish by about Nov 4. Delta is the fallback.

## Decisions I made for you (say if you object)

1. **Neutral-Clause Twin** as the honest comparison for v2, paired by instance id. No matched honest instructions.
2. **"Pressure reader" becomes an assignable role** for v2 cells, with its criteria written into the role document
   before any role is assigned. I report the criteria text to you before it is applied.
3. **Caps:** 35 H100 GPU-h on Bridges-2 and 18 GPU-h on Delta (12 fallback, 6 for seeds).
4. **Branch push:** `mechanism-analysis` goes to GitHub so Bridges-2 can pull it. No merge to main.
5. **Phases back to back**, with each reading posted to you before the next phase's GPU work.
6. **Seeds are conditional:** they run only if a headline claim rests on the identities of the mechanism-specific
   heads.
7. **Records:** analysis cells stay on Delta, and curated tables go into the repo under
   `docs/research/mechanism-analysis/`.
8. **Role-criteria amendment** for v2: neutral-twin columns and one new prompt Segment, dated and logged.
9. **The FAR-vs-others lens prediction is exploratory.** FAR's clauses all name the act, so wording and mechanism
   cannot be separated.
10. **The instructed-inversion control is added** as a new test condition. The existing datasets are untouched.
