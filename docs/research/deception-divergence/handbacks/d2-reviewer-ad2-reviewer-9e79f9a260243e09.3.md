# Last message of d2-reviewer ad2-reviewer-9e79f9a260243e09 (2026-11-02T22:43:15-05:00)

I added a "Hand-back check" section to the D2 review. The worker's four claims are all correct, and the review's verdict and recommendations are unchanged. The file passes the lint check.

**The records copied under `results/d2/` are identical to the originals.** That covers the five judge ledgers, the five label files with their manifests, and the final readings in both formats.

| Worker's claim | What the data shows |
|---|---|
| The Sonnet cross-check has 7 disagreements, all involving UNCLEAR | Correct. Three go from CORRECTED to UNCLEAR, one from MAINTAINED to UNCLEAR and three from UNCLEAR to CORRECTED. No row flips between MAINTAINED and CORRECTED. |
| The first-token proxy is vacuous because every maintenance list is empty | Correct. Its agreement with the judge is just the share of corrected rows, for example 572 of 579 on FAR. |
| The plan's section 3b trigger fired because "I" opens most calibration rows | Correct. "I" opens 112 of 190, 125 of 177 and 188 of 190 decided calibration rows. |
| The ledger ceilings sum to $21, above the $20 cap, though spend was $2.71 | Correct. Settled cost sums to $2.7071 over 4,064 calls, with nothing unsettled. |

The ceiling point is a process gap rather than a spend problem: the per-stage ceilings did not enforce the direction's cap. Only the low actual cost kept spend at about 13.5 percent of it.

**The hand-back's numbers all match mine, and the review notes four points to change:**
- **One overstatement.** Its first caveat says nothing in the data tells the instruction clause apart from a lie-maintenance state. One subset partly does: on rows whose inversion clause names the wrong answer, as D's does, D and I do not differ. The gap is 0.005 on FAR's 210 such rows and 0.000 on SDR's 35, which points to the clause.
- **Three omissions.** It does not split the gap by the inversion clause's form. It does not measure the margin behind "passes by one point": 13 of the 40 misses sit within one logit of the threshold. It does not mention that many of D's unclear labels are refusals, which appear almost only under D.
- **An unprovable record.** Its claim that the proxy hash was recorded before the main judge stage fits the file times. The ledgers carry no timestamps, so it cannot be proven. It also does not flag that the classifier's test rows were read before the hash was recorded.

The summary has gone to the lead.

File: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reviews/04-d2-review.md`
