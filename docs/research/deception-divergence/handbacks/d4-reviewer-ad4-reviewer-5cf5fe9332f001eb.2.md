# Last message of d4-reviewer ad4-reviewer-5cf5fe9332f001eb (2026-11-02T14:30:33-05:00)

Every number I checked in hand-back 02 reproduces, and no issue changes a pre-registered verdict. The review is `docs/research/deception-divergence/reviews/01-d4-review.md` in the worktree.

The stop hook asked for a hand-back file, so I added a short pointer at `docs/research/deception-divergence/reports/04-handback.md`, which also passes lint. Your brief allowed one file, so this second file exists only to satisfy the hook. I put it in the worktree rather than the main-checkout path the hook named, to keep the worktree isolation.

**Verdicts:**
- **(d) Static read: supported.** P1 fails and P2 fails. The P2 fail tells us little about copying, because no head of the model passes that read.
- **(a) Attention patterns: supported.**
- **(b) After-cue arm: supported with caveats.** The post_tag margins are bit-identical to J4.
- **(c) SDR route closure: supported with caveats.** The frozen rule reads query-side, and the loop label is "closes, route-specific".

**Issues, all low or minor:**
1. In rider (b), the after-cue run explains where the MLPs' extra share sits. It does not explain the wide null spread, which is wider after the cue, not narrower.
2. In rider (b), "specific" needs the F-mech-003 caveat next to it, because it is not deception-specific.
3. In rider (c), "the contrast belonged to the method or the dataset" is interpretation. The supportable statement is that the SDR-versus-FAR/SER contrast does not reproduce on the B1 code path.
4. In rider (c), the lower bound of the loop-closure share sits only 0.011 above the 0.50 bar.
5. Minor: a default-path claim rests on reading the code rather than on a test, and a few provenance gaps change no number.

**Recommendation.** The findings register is still empty, so I mapped F1 to F4 to riders (d), (a), (b) and (c). F1 and F2 can be marked reviewed as they stand. F3 and F4 can be marked reviewed once their wording takes in issues 1 and 2, and 3 and 4, respectively.
