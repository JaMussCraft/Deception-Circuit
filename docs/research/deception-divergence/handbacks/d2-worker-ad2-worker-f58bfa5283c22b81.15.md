# Last message of d2-worker ad2-worker-f58bfa5283c22b81 (2026-11-02T23:12:44-05:00)

I revised the D2 follow-up plan with the lead's six decisions and sent it back to the lead. It is lint clean, and I wrote no code and ran no job or git command.

The plan is at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/plans/D2-followup-plan.md`.

| Figure | Value |
|---|---|
| Rows (forwards) | 4,636 |
| GPU-hours at D2's measured rates | 0.41 |
| GPU-hours by D2's model constant | 0.59 |
| Reserved, 40 minutes on one Bridges-2 H100 | 0.67 |

- **The design is now a 2×2.** HT is added next to DT. A joint table says what each pattern of the two means: instruction content, compliance, "has lied", or a signal specific to HI. The DT and HT rates are always reported together.
- **The primary reading is fixed in advance.** It is FAR act-form, with 210 ids in 12 clusters. SDR act-form, with 35 ids in 7 clusters, is secondary. SER is excluded.
- **The mirror pick is recorded as a deviation** from the inversion builder's random draw. The draw stays as a fallback. The manifest reports how often it fires, which was zero in the scratch check.
- **Every clause pair now shows its form and token result.** All 49 pairs in use have equal clause token counts and a zero full-prompt difference on all 1,909 rows that use them. These come from a scratch run, and the real dry run must reproduce them. The 50th pair, SER 05, is in the pool but no id uses it.
- **Twelve pairs are marked borderline**, each with a reason. The first draft listed eleven, and SDR 04 was added on re-reading. No FAR pair is borderline, so the primary reading does not depend on that review.
- **Two decisions are written in as exclusions.** The SDR extension and the refusal share are out.

Two questions remain for the lead. If the independent reviewer rewrites a mirror, the dry run must re-check it before ruling R15. The lead may also want a sensitivity reading that leaves out the pairs whose honesty is indirect.

Code waits for the lead's confirmation and ruling R15.
