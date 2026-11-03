# Last message of d4-reviewer ad4-reviewer-5cf5fe9332f001eb (2026-11-02T14:30:09-05:00)

Every number I checked in hand-back 02 reproduces, and none of the issues I found changes a pre-registered verdict. The review is written and passes lint at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reviews/01-d4-review.md`.

**Verdicts**
- **(d) Static read: supported.**
  - P1 fails. head.14.4 ranks 24 of 320 against a cutoff of 16, and layer 15's sum is only fourth.
  - I recomputed all 320 scores from the safetensors weights and they match to 1e-15.
  - P1 still fails under every reading matrix and without folding the RMSNorm gammas.
  - P2 fails, but the read cannot detect copying on this model. No head of the 1,024 reaches 0.5, and the identity map scores 0 because the embeddings are untied.
  - The 82 item tokens are the leading-space tokens the datasets actually score.
  - All four quartet heads share KV group 6.
- **(a) Attention patterns: supported.**
  - Both tasks use exactly the 100 held-out ids, paired on the D and twin sides.
  - I reproduced every shift, rank and segment mass.
  - The new flag leaves the default path on the same loaders.
- **(b) After-cue arm: supported with caveats.**
  - The arm excludes exactly the 7 differing cue tokens and covers the 23 positions after them.
  - The post_tag margins are bit-identical to J4 and its supplement, so post_tag reproduces 0.724 and 0.498.
  - After-cue f is 0.662 for S_all and 0.582 for heads_only, both recomputed with their intervals and null maxima.
  - No null draw contains a head member, as R10 and R10a require.
- **(c) SDR route closure: supported with caveats.**
  - The batch file is a faithful clone of B1-far with SDR operands only.
  - The pre-registered rule reads query-side: r_Q minus r_K is 0.526 against 0.15.
  - Under R1 and R9, T1 is "closes, route-specific", with offline M_q 0.546 (interval 0.511 to 0.577).
  - Gates G1 to G3 pass.

**Issues**
1. **Low, rider (b).** The claim that the run "answers the F-rte-008 caveat" holds for the MLP share, which falls from 0.226 to 0.080. It does not hold for the null spread: the S_all null standard deviation is wider after the cue, 0.329 against 0.250. The MLP share is also a difference of non-additive arms, since no run patches the three MLPs alone.
2. **Low, rider (b).** "Shared and specific" after the cue means specific against random heads given the same MLPs. Per F-mech-003 it is not deception-specific, so that caveat belongs in the same sentence.
3. **Low, rider (c).** "The contrast belonged to the method or the dataset" is interpretation. F-sdr-012's routing pilot measured a different quantity. The supportable statement is that the contrast does not reproduce under the B1 code path.
4. **Low, rider (c).** M_q's lower bound sits only 0.011 above the 0.50 bar, so any SDR-closes versus FAR/SER-bypass statement should carry the interval.
5. **Minor.** The "byte-for-byte as before" default-path claim rests on reading the code, not on a test. The provenance gaps (the hashed dataset_dict.json is identical across tasks and does not pin the item data; attention_patterns.py is unhashed) and the leftover dry-run backup files change no number.

**Recommendation.** The findings register in WORKLOG.md is empty, so I mapped F1 to F4 to riders (d), (a), (b) and (c), in the hand-back's order. F1 and F2 can be marked reviewed as they stand. F3 and F4 can be marked reviewed once their wording takes in issues 1 and 2, and 3 and 4, respectively.

My recompute scripts are in `/u/swong2/.claude/jobs/5b9b1c28/tmp/`. A setup hook asked for a separate hand-back file, but I did not write one because your brief allowed only this file.
