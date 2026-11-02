# Review 07: B3 J4, the transfer test on sycophancy alone

Independent Opus review, Sun 1 Nov 2026, of Slurm job 23415595 (Delta, A100, host gpua055, 2,356 s after the model
load). I read spec.md (rulings R5, R10, R10a, R11 and R12), plan B3 sections 2 to 4, review 03, hand-backs 18, 31 and
33, the code, the log and the three output files. I recomputed every number below from `margins.json` with my own
NumPy code. The recompute imports no project code, and it re-draws the nulls with its own port of the draw loop. The
span check imports only the prompt builder, to build the inputs. CPU only, mgnp interpreter, BLAS threads 1, no git,
no Slurm. The scripts and logs are in the job tmp directory, `/u/swong2/.claude/jobs/230e4716/tmp/j4rev_*`. They are
outside the repository and are not meant to be committed.

## Verdict

**Confirmed: shared, non-specific, under R5 as R11 applies it.** The rule number f_syc(S_all) at post_tag is 0.724
(bootstrap 0.702 to 0.746). That is in the shared band. The largest of the 20 member-excluded null draws is 0.505
(draw 11), which reaches the 0.5 that R5 labels non-specific. Every number reproduces exactly. Pass 1, the clean and
uncued margins and every readout arm shared with J3 are bit-identical to J3.

The label is pre-registered and stands, but it is thin. One draw carries it: its own interval is 0.467 to 0.541, and
the next draw is 0.442. S_all still exceeds all 20 draws, by 0.219. The null spread is the story here: random 32-head
draws with the same three MLPs range from -0.430 to 0.505 at post_tag. Most of that spread comes from patching across
the cue's own tokens. The verdict carries the plan section 4 label, "a cue-driven, non-instructed falsehood, not
spontaneous deception", and the F-mech-003 caveat.

The supplement run (job 23416459: heads_only, S_far and S_ser) changes how the verdict should be read, though not the
verdict itself. Check 6 has the numbers.

- **The heads beat random heads; the MLPs carry the qualifier and the band.** S_all's 32 heads alone remove 0.498
  (0.470 to 0.526). That is 0.227 above the largest of their 20 heads-only null draws, 0.271, and no draw comes near
  0.5. So the non-specific label comes from the three shared early MLPs combined with random heads, not from S_all's
  heads. The same MLPs also lift S_all from 0.498 into the shared band: the heads alone sit 0.002 under 0.50, with an
  interval that straddles it.
- **The specific transfer is in S_far and the quartet.** S_far removes 0.393 against a null maximum of 0.276. It holds
  Gupta's writer L15H8 but no quartet head. S_ser removes 0.197, and 3 of its 20 null draws exceed it (maximum 0.586).
  So S_ser shows no effect distinguishable from random layer-matched sets.

## Checks

### 1. Recompute from margins.json: every stored number reproduces

Kept rows are `kept_rows` (530). C, T and K are the pass-2 cued, uncued and patched margins, with m = logit(X) −
logit(gold). f = (mean C − mean K) / (mean C − mean T). The reversal share is the patched argmax equal to gold over
the 154 flips. The bootstrap is `default_rng(0).integers(0, 530, (2000, 530))` with the 0.025 and 0.975 quantiles.

| arm | f (kept) | 95% CI | f (flips) | reversal | null f max (draw) | null reversal max |
| --- | --- | --- | --- | --- | --- | --- |
| S_all post_tag | 0.7241 | 0.7017 to 0.7463 | 0.914 | 0.942 (145/154) | 0.5051 (11) | 0.851 |
| S_all readout | 0.4532 | 0.4354 to 0.4689 | 0.570 | 0.610 | 0.2178 (10) | 0.162 |
| S_q post_tag | 0.3315 | 0.3109 to 0.3522 | 0.532 | 0.604 | 0.0212 (15) | 0.013 |
| S_q readout | 0.2502 | 0.2333 to 0.2659 | 0.381 | 0.390 | 0.0129 (00) | 0.006 |
| gupta6 post_tag | 0.4860 | 0.4667 to 0.5053 | 0.645 | 0.734 | 0.1798 (15) | 0.182 |
| gupta6 readout | 0.3399 | 0.3242 to 0.3553 | 0.455 | 0.474 | 0.1392 (13) | 0.117 |
| gupta_writers post_tag | 0.4566 | 0.4367 to 0.4752 | 0.627 | 0.714 | 0.0770 (19) | 0.045 |
| gupta_writers readout | 0.3116 | 0.2966 to 0.3264 | 0.432 | 0.448 | 0.0549 (19) | 0.013 |
| L17H24 post_tag | 0.2152 | 0.2000 to 0.2303 | 0.363 | 0.409 | 0.1760 (02) | 0.143 |
| L17H24 readout | 0.1438 | 0.1317 to 0.1559 | 0.248 | 0.182 | 0.1418 (02) | 0.091 |

Every f, CI, f over flips, reversal share and null maximum equals the stored value to four decimals. The R5 band is
shared: 0.724 is at least 0.50. The R11 non-specific condition is met on the member-excluded draws: 0.5051 is at
least 0.5, and exactly one of the 20 draws reaches it.

The orchestrator's reading is right, with one small correction. Four S_all post_tag draws are below −0.1: −0.400,
−0.430, −0.371 and −0.139. A fifth, draw 19, is −0.097.

The pass bar of plan section 2 still passes on the new member-excluded draws. gupta6 at the readout reverses 0.474,
against a null maximum of 0.117 (J3 had 0.084 on its overlapping draws).

### 2. Pre-registration: all items met

- **Sets.** The default syc sets are the ones R11 names for J4: gupta6, gupta_writers, L17H24, S_q and S_all. R11 lists
  heads_only, S_far and S_ser as reported and non-deciding, and those are in the supplement. S_all has 35 members:
  32 heads in layers 7 to 17 (two in layer 7, three in 8, six in 9, six in 10, five in 11, four in 13, one in 14,
  L15H8, and L17H24 to L17H27), plus mlp.5, mlp.6 and mlp.7.
- **post_tag span.** `SycPair.cue_start` is the first differing token, and `arm_mask("post_tag")` covers cue_start
  through the Readout inclusive. This is what R11 defines. I rebuilt all 800 twins with the cached tokenizer:
  - Every item uses the first neutral sentence.
  - The differing window is 7 tokens: " think the answer is (X)," against " have been thinking about this question,".
  - The span is 30 positions on every item. It starts at " think", because the opening "I" is shared, and it ends at
    the "(" of the prefill. The 23 positions after the differing window are shared tokens: " but I'm curious what you
    think.", the instruction, the end of the turn, the assistant header and "The answer is (".

  So post_tag patches the cue tokens themselves as well as everything downstream of them (see check 3).
- **Nulls.**
  - My own port of the draw loop (`random.Random(seed)`, sorted (kind, layer) keys, pools without mlp.0 and without
    head members) reproduces all 200 recorded draws exactly, for all five sets and both arms. The seeds are 20261025
    (S_all), 20264025 (S_q), 20265025 (gupta6), 20267025 (gupta_writers) and 20268025 (L17H24), which is NULL_SEED
    plus 1000 times the SET_ORDER index.
  - Every draw has its set's (kind, layer) histogram, and no draw holds a head member of its own set.
  - `null_kept_members` is mlp.5.0, mlp.6.0 and mlp.7.0 for every S_all draw and empty for the head-only sets, as
    R10a requires. Each set record says "R10a: head members excluded, MLP members kept".
- **Pass 1 identical to J3.** The cued and uncued argmaxes, the kept, flip and kept_rows lists, and both pass-1 margin
  vectors are bit-identical to J3, on a different A100 node (maximum absolute difference 0.0). The pass-2 clean and
  uncued margins are also bit-identical. So are the patched margins of every arm the two runs share (gupta6,
  gupta_writers, L17H24, S_q and S_all at the readout). Pass 1 gives 530 kept and 154 flips. The drift between pass 1
  and pass 2 is the same as in J3: up to 0.19 on the cued margin and 0.33 on the uncued margin. No flip or kept item
  changes class.
- **Manifest.**
  - `git_commit` is 21bc397a304f778131214d41191e3392f125481f (40 hex), with `git_dirty` false.
  - The manifest also records the Slurm job id, the host, the model revision, the software versions and the argv
    (`--task syc --positions post_tag,readout`).
  - All seven `code_sha256` entries and both dataset hashes equal `sha256sum` of the current files. stats.py
    (a9d280bc…) and b3_patch.py (c95ced73…) are the post-R10 versions of hand-back 31.
  - `grader` is null, which is right for a run with no judge.
  - The bootstrap settings are seed 0, n_boot 2000 and n_null 20.
- **Parity.** The `knockout.py` parity check, which review 03 found missing, has since run (job 23415522,
  `outputs/_studies/b3/parity/parity.json`). The patching wrapper and `knockout.py` agree exactly on 10 FAR held-out
  ids: 0.8849 at the post-clause positions and 0.9835 at all positions, with an absolute difference of 0.0. This
  closes review 03's problem 2.

### 3. The S_all nulls: wide spread from a large set patched over the cue tokens

The 20 S_all draws at post_tag, each 32 non-member heads plus mlp.5 to mlp.7:

| draw | f post_tag (95% CI) | reversal | kept non-flips lost (to X) | f readout |
| --- | --- | --- | --- | --- |
| 11 | +0.505 (+0.467 to +0.541) | 0.851 | 7 (1) | +0.122 |
| 10 | +0.442 (+0.405 to +0.477) | 0.766 | 12 (5) | +0.218 |
| 02 | +0.289 | 0.727 | 22 (10) | −0.195 |
| 09 | +0.279 | 0.662 | 11 (6) | −0.067 |
| 05, 08, 01, 06 | +0.132 to +0.149 | 0.49 to 0.53 | 16 to 28 | −0.07 to +0.21 |
| 12, 03, 00 | +0.037 to +0.067 | 0.34 to 0.50 | 25 to 33 | +0.06 to +0.12 |
| 18, 13, 04, 17, 19 | −0.097 to −0.009 | 0.25 to 0.43 | 28 to 45 | −0.14 to +0.15 |
| 16 | −0.139 | 0.279 | 53 (44) | −0.176 |
| 15 | −0.371 | 0.188 | 93 (82) | −0.366 |
| 07 | −0.400 | 0.136 | 78 (72) | +0.103 |
| 14 | −0.430 | 0.162 | 98 (85) | −0.518 |

The null distribution has mean 0.034 and SD 0.250. For S_all itself, 3 of 376 kept non-flips lose gold.

The spread grows with set size, and the readout arm is narrower than post_tag:

| null set | SD at post_tag | SD at readout |
| --- | --- | --- |
| S_q (4 heads) | 0.008 | 0.007 |
| gupta6 (6 heads) | 0.092 | 0.066 |
| S_all (32 heads and 3 MLPs) | 0.250 | 0.190 |

What drives it:

- **No known cue-route head in the top draws.**
  - Draws 10 and 11 hold no gupta6 head and no quartet head. The quartet and L15H8 are S_all members and are excluded.
    L16H19, L18H28 and L20H14 sit in layers S_all does not occupy.
  - The only drawable gupta6 head is L15H11, in the single layer-15 slot, and it appears only in draw 01 (f 0.136).
  - Draw 10's layer-17 heads are H0, H10, H18 and H21. Draw 11's are H1, H4, H11 and H31.
  - The overlap concern that R10 fixed for each set's own members does not reappear through gupta6 or S_q heads here.
- **The shared MLPs lift the null, but they do not make it wide.** All 20 draws contain mlp.5 to mlp.7, yet the
  draws range from −0.430 to 0.505. The supplement's heads-only null (check 6) has no MLPs and is just as wide, with
  SD 0.280 and a range of −0.703 to 0.271. But its mean is −0.072 against 0.034 with the MLPs, and its maximum is
  0.271 against 0.505. So the MLPs raise the null by about 0.1 on average and carry its top draw over 0.5, while the
  width comes from the heads. The two nulls use different seeds, so this comparison is not paired draw by draw.
- **No single high-leverage head stands out.** I compared each head's mean draw f with and without it, over the heads
  that appear in at least three draws. The largest gaps are about ±0.3, both up (L11H6, L13H18, L10H0) and down
  (L10H30, L11H26). With 20 draws and 32 heads each, that is noise-level, not an identification.
- **The likely source is the span.** post_tag starts on the 7 differing cue tokens. At those positions, 22 of S_all's
  32 heads (layers 7 to 11) and three early MLPs largely encode the current token. Writing their uncued-twin values
  there partly substitutes the neutral sentence's token content into the cued run. The result can remove the cue
  (draw 11) or produce hybrid states that push toward the cue letter (draws 07, 14 and 15 send 72 to 85 kept non-flips
  to X).
  - The readout arm, which avoids the cue tokens, has a narrower null (SD 0.190, maximum 0.218).
  - Post_tag and readout f correlate only 0.54 across draws.
  - No arm patches only the shared positions after the cue window, so this explanation is inferred, not measured.
- **Flip reversal does not discriminate for a set this large.** Draws with f near zero (00, 03, 13, 18) still reverse
  0.34 to 0.43 of flips and break 28 to 33 non-flips. Reversal on near-tie flips (median cued margin 1.71) mostly
  measures perturbation size. S_all's 0.942 against a null maximum of 0.851 should not be read as specificity
  evidence. S_all's low non-flip damage (3 of 376) is the better sign that it removes the cue rather than scrambling.

**Where the transfer sits.**

| set at post_tag | f |
| --- | --- |
| S_all | 0.724 |
| gupta6 | 0.486 |
| gupta_writers | 0.457 |
| S_q | 0.331 |
| L17H24 alone | 0.215 |

- The per-item effects C − K correlate 0.84 (S_all with S_q), 0.88 (S_all with gupta6) and 0.92 (S_q with gupta6).
- Every flip that S_q or gupta6 reverses is also reversed by S_all (116 of 116), and S_all reverses 29 more.
- S_all contains the whole quartet and two of Gupta's writers (L17H24 and L15H8). L15H8 and L15H11 together add about
  0.24 to L17H24 alone.
- So at least the quartet's 0.331 is inside S_all's 0.724, and plausibly much of the Gupta writer route.
- The remaining 0.39 comes from S_all's other 26 heads and the three MLPs, non-additively. Those include the FAR and
  SER members in layers 7 to 14, which are exactly the early heads whose random counterparts make the null wide.
- The supplement (check 6) splits this remainder:
  - The three MLPs add 0.226: S_all removes 0.724 and its heads alone 0.498.
  - S_far, which holds L15H8 but no quartet head, removes 0.393 and beats all its draws.
  - S_ser, which holds neither L15H8 nor a quartet head, removes 0.197, inside its null.
- So the specific transfer sits in the quartet and the FAR set, and S_far's share includes Gupta's writer L15H8.

### 4. What the result licenses

The plan section 4 label applies: sycophancy is a cue-driven, non-instructed falsehood, not spontaneous deception. The
model may believe the user, and nothing in this task elicits a belief-contrary statement it knows to be false.

**What "shared, non-specific" licenses:**

- The union of the FAR and SER deciding sets and the quartet, patched from the cue through the Readout, carries most
  of a user cue's pull toward a wrong MMLU answer. That is 0.72 of the mean margin shift and 145 of 154 flips, with
  little collateral damage.
- The quartet that carries the instructed pressure on FAR and SER (F-rte-005, F-rte-006) also carries a third of this
  non-instructed cue's effect. Its null is tight: four random layer-17 heads reach at most 0.021.
- The FAR deciding set alone removes 0.393 against a null maximum of 0.276. S_all's heads remove 0.498 against a
  heads-only null maximum of 0.271.
- So the cue route these sets implement is not confined to operator instructions. It also serves a user's stated
  opinion.

**What it does not license:**

- **Deception-specific machinery.** F-mech-003 already shows the sets carry transparent inversion, and sycophancy is
  not deception.
- **That the SER set carries any of it.** S_ser's 0.197 is exceeded by 3 of its 20 draws.
- **That the FAR set's share is separate from Gupta's route.** S_far contains L15H8, one of Gupta's writers.
- **That S_all as a whole is specific among sets of its size and layers.** One of 20 random 32-head draws with the
  same MLPs reaches 0.505 at post_tag. The label is pre-registered.
- **That the shared band holds without the early MLPs.** The heads alone give 0.498, 0.002 under the bar.
- **Anything about alignment faking**, whose premise failed (F-rte-007).

**What is new at post_tag.** J3 already showed S_all at the Readout: 0.453 here and bit-identical in J3. J3's null
maximum on overlapping draws was 0.327; on member-excluded draws it is 0.218, so the readout arm is specific by a
clear margin. Post_tag raises the set's f to 0.724, about 1.6 times the readout value. S_q and gupta6 rise by similar
ratios (0.250 to 0.331, 0.340 to 0.486). So much of what these sets mediate is written before the Readout, at the cue
and the positions after it. But the null maximum rises more than the set's f, from 0.218 to 0.505. In relative terms
the post-cue arm is less specific than the readout arm: the ratio of f to null maximum is 1.4 at post_tag and 2.1 at
the readout. R11 makes post_tag the rule arm, so the verdict is "shared, non-specific". The readout arm does not decide.
On it, S_all's 0.453 would fall in the partial band, and it exceeds its null maximum clearly.

### 5. The estimator, the sign, the filtering and the bootstrap: nothing changes the verdict

- **Ratio of means.** The denominator is mean C − mean T = −2.063 − (−5.303) = 3.240 logits, far from zero. 12 kept
  items have C < T and 18 have |C − T| under 0.5. No per-item ratio is infinite (0 `None` entries in every main
  arm).
  - The per-item median ratio for S_all at post_tag is 0.781.
  - f over items with |C − T| of at least 1 is 0.741.
  - f over the 154 flips is 0.914, and f over the 376 kept non-flips is 0.619.
  - The probability-scale f is 0.954, but it saturates near 1.
  - Every variant stays at or above 0.50.
- **Sign.** C > T on average, and m rises toward the cue letter, so positive f means the patch moves the cued run
  toward its uncued twin. The convention matches J3 and plan section 2.
- **Kept-item filtering.** Kept items are fixed in pass 1 and are identical to J3. Every kept item has a negative
  pass-2 uncued margin and every flip a positive pass-2 cued margin. Two kept non-flips have a positive pass-2 cued
  margin, as in J3.
- **Bootstrap clustering.**
  - Items are independent: one question, one seeded cue letter and the same neutral sentence each. So the item
    bootstrap the plan specifies is appropriate.
  - The one plausible cluster is the MMLU subject (56 among kept items). As a sensitivity check, a subject-clustered
    bootstrap (2,000 resamples, seed 1) gives 0.669 to 0.770 for S_all and 0.292 to 0.371 for S_q. Both stay in
    their bands.
  - Clustering by cue letter or by neutral sentence is not meaningful here: only one neutral sentence is used.

### 6. Supplement: heads_only, S_far and S_ser

**The run.**

- The job is 23416459 on an A100 (host gpua034), with 1,455 s of compute after the model load.
- The command is `--task syc --sets heads_only,S_far,S_ser --positions post_tag,readout`, with 20 null draws per set.
- The manifest's `git_commit` is c32627e37900e23a63f3deb8d1b955182700647b (40 hex), with `git_dirty` false.
- All seven `code_sha256` entries and both dataset hashes equal `sha256sum` of the current files. They are the same
  hashes as the main J4 run.
- Pass 1, the kept, flip and kept_rows lists, and the pass-2 clean and uncued margins are identical to J4's.
- The recompute is `j4rev_supp.py` and `j4rev_supp2.py`, which import no project code.
  - It reproduces every stored f exactly.
  - It re-draws all 120 null draws exactly: seed 20266025 for heads_only, 20262025 for S_far and 20263025 for S_ser.
  - No draw holds a head member of its own set.
  - The kept MLPs are none for heads_only, mlp.6 and mlp.7 for S_far, and mlp.5 for S_ser, as R10a requires.

| arm | f (kept) | 95% CI | reversal | non-flips lost | null f max (draw) | draws above the set | null mean, SD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| heads_only post_tag | 0.4984 | 0.4699 to 0.5262 | 0.805 | 3 | 0.2706 (07) | 0 | −0.072, 0.280 |
| heads_only readout | 0.4006 | 0.3831 to 0.4169 | 0.565 | 4 | 0.1859 (07) | 0 | −0.010, 0.155 |
| S_far post_tag | 0.3928 | 0.3588 to 0.4249 | 0.630 | 8 | 0.2761 (07) | 0 | −0.170, 0.270 |
| S_far readout | 0.3085 | 0.2937 to 0.3220 | 0.331 | 9 | 0.1914 (07) | 0 | 0.046, 0.119 |
| S_ser post_tag | 0.1974 | 0.1624 to 0.2318 | 0.377 | 17 | 0.5857 (17) | 3 | −0.161, 0.430 |
| S_ser readout | 0.1246 | 0.1106 to 0.1396 | 0.149 | 13 | 0.3032 (17) | 3 | −0.018, 0.235 |

**What it settles.**

- **The non-specific label comes from the MLPs, not the heads.** S_all's 32 heads beat every heads-only draw by 0.227.
  The top heads-only draw is 0.271 (interval 0.248 to 0.293), and no draw reaches 0.5. With mlp.5 to mlp.7 added to
  both the set and its draws, the set rises to 0.724 and the top draw to 0.505.
  - So the one-draw label should be read as "random heads, given the same three early MLPs, can reach half the effect".
    It should not be read as "S_all's heads are no better than random".
  - The same MLPs move S_all over the band boundary. The heads alone give 0.498, and their interval of 0.470 to 0.526
    straddles 0.50. So both the band and the qualifier hinge on the early MLPs at the cue positions.
- **The width of the null comes from the heads.** The heads-only null is as wide as the MLP-sharing one, with SD
  0.280 against 0.250. S_ser's null (19 heads in layers 7 to 14, plus mlp.5) is the widest, with SD 0.430 and a range
  of −1.020 to 0.586. This fits the explanation in check 3: early-layer heads interchanged over the cue tokens perturb
  the readout strongly in both directions. Every null is narrower at the readout.
- **S_far carries a specific share; S_ser does not.**
  - S_far removes 0.393, beating all its draws by 0.117. It holds L15H8, one of Gupta's writers, and no quartet head.
  - S_ser removes 0.197. That is under 0.25, and it ranks fourth among its 20 draws, at both arms (draws 17, 15 and 00
    exceed it at post_tag).
  - S_ser shares 9 members with S_far, but not L15H8.
- **S_ser's null maximum above the set itself needs a caveat.** Read it as "the SER deciding set shows no transfer
  distinguishable from random layer-matched sets". The SER set's non-FAR members are not shown to add anything to
  S_all. The arm does not decide, so the verdict is unaffected.

The seeds differ between the heads-only null and the MLP-sharing null, so comparing them is by distribution, not draw
by draw. No MLP-only arm exists, so the MLPs' own effect is inferred as S_all minus heads_only (0.226), and that
difference is not additive in general.

## Problems found

Severity-ordered. None changes the verdict.

1. **The non-specific label rests on one draw (medium, interpretation).** Draw 11 is 0.505 with interval 0.467 to
   0.541. The next draw is 0.442, and S_all exceeds every draw. The label is pre-registered and correct as applied,
   but the row should give the null maximum, its draw and how thin the crossing is, so the label is not read as "S_all
   is no better than random". The heads-only arm shows the label comes from the shared MLPs: S_all's heads beat every
   heads-only draw (0.498 against at most 0.271).
2. **The rule arm patches the cue tokens themselves (medium, interpretation).** post_tag starts on the 7 differing cue
   tokens, as R11 defines it. A large set of early-layer components interchanged there partly substitutes the cue's
   token content, which explains the wide null (SD 0.250 against 0.190 at the readout) and the large negative draws.
   No arm patches only the 23 shared positions after the cue window. That arm, by analogy with the "after the clause"
   arm of F-rte-002, would separate carrying the cue forward from reading the cue tokens. It is not required by R11.
   It would be a cheap follow-up: S_all and its 20 draws on 530 items is about 0.2 h on an A100, including the
   model load. Patching code for that span does not exist yet. The supplement makes this more pressing. The shared
   band depends on mlp.5 to mlp.7, and early MLPs at the cue tokens are the components most likely to act as token
   substitution.
3. **Flip reversal is not a specificity measure for S_all (low, reporting).** Null draws with f near zero reverse 0.34
   to 0.43 of flips. Report reversal beside f with the non-flip damage (S_all 3 of 376; null draws 7 to 98), or not
   at all for S_all.
4. **The R11 verdict is not machine-written (low, bookkeeping).** `syc_results` computes the pass bar but no
   `transfer_verdict`, so the "shared, non-specific" label for J4 exists only in the orchestrator's reading. The
   readings file or the finding should state the rule number, the band, the null maximum and the label explicitly.
5. **results.json still loses the set-to-null-label mapping (low, carried over from review 03, problem 3).** The
   `nulls` summaries overwrite the label lists. `margins.json` keeps them, and `null_draws` and `null_kept_members`
   are now in both files, so the draws can be tied to labels by name.
6. **The shared band rests on the three early MLPs (medium, interpretation; from the supplement).** S_all's heads alone
   give 0.498 (0.470 to 0.526), just under 0.50. The verdict is about S_all as R11 defines it and stands. But the row
   should say the heads alone sit at the band boundary.
7. **S_ser does not beat its own null (low, reporting; from the supplement).** S_ser's 0.197 is exceeded by 3 of its
   20 draws (maximum 0.586) at post_tag, and again by 3 at the readout. The row should report S_ser as showing no
   specific transfer, not as a smaller effect.

## Proposed finding text

Row F-rte-008, in the F-rte-002 shape, with the supplement folded in:

> Does the instructed route carry a non-instructed, cue-driven falsehood (B3 transfer on sycophancy alone, R11):
> shared, non-specific; interchanging S_all (the FAR and SER deciding sets and the layer 17 quartet: 32 heads in
> layers 7 to 17 and mlp.5 to mlp.7) with its uncued-twin outputs from the cue's first differing token through the
> readout removes 0.724 (bootstrap 0.702 to 0.746; 0.669 to 0.770 clustered by 56 MMLU subjects) of the cue-induced
> shift of logit(cue letter) minus logit(gold) over the 530 of 800 MMLU items answered correctly without the cue, and
> reverses 145 of 154 cue-induced flips while 3 of 376 other kept items lose the right answer; it exceeds all 20
> layer-matched draws of 32 non-member heads with the same three MLPs, but the largest, 0.505 (draw 11, interval
> 0.467 to 0.541; next 0.442), reaches the 0.5 at which R5 labels the result non-specific. Both the label and the
> band rest on the three shared early MLPs: S_all's 32 heads alone remove 0.498 (0.470 to 0.526), against at most
> 0.271 for 20 heads-only draws. The specific transfer sits in the FAR set and the quartet: the FAR deciding set
> removes 0.393 (null maximum 0.276) and the quartet 0.331 (null maximum 0.021), while the SER deciding set's 0.197
> is exceeded by 3 of its 20 draws (maximum 0.586), so it shows no specific transfer; Gupta et al.'s six heads remove
> 0.486 (null maximum 0.180), every flip that they or the quartet reverse S_all also reverses, and at the readout
> alone S_all removes 0.453 against a null maximum of 0.218. Sycophancy here is a cue-driven, non-instructed
> falsehood, not spontaneous deception, and per F-mech-003 the sets also carry transparent inversion, so "shared"
> means a shared cue route, not deception-specific machinery. Caveats: the non-specific label rests on one draw 0.005
> over the bar; the post-cue span includes the 7 differing cue tokens, where random draws of early-layer heads swing
> widely in both directions (null SD 0.250 for S_all, 0.280 heads-only, 0.430 for the SER set, against 0.190 for
> S_all at the readout), so flip reversal does not discriminate for these sets (S_all draws with f near zero reverse
> 0.34 to 0.43 of flips), and no arm patches only the positions after the cue window, which would test whether the
> early MLPs act as token substitution; the FAR set contains Gupta's writer L15H8, so its share is not separated from
> Gupta's route; the MLP contribution (0.226) is inferred as S_all minus its heads, from nulls with different seeds;
> one prompt, one cue type and one neutral sentence, on MMLU only.

Evidence:

- `outputs/_studies/b3/j4_syc/results.json`
- `outputs/_studies/b3/j4_syc/margins.json`
- `outputs/_studies/b3/j4_syc/run_manifest.json`
- `outputs/_studies/b3/j4_syc_supplement/results.json`
- `outputs/_studies/b3/j4_syc_supplement/margins.json`
- `outputs/_studies/b3/j4_syc_supplement/run_manifest.json`
- `outputs/_studies/b3/parity/parity.json`
- `docs/research/instructed-route/reviews/07-j4-review.md`

**Commit.** The deciding run is at 21bc397 and the supplement at c32627e, and the code hashes are identical. The
commit field should name 21bc397, the commit of the run that decides. The supplement manifest in the evidence carries
c32627e.

**Strength.** "reviewed" is right. The run follows R11 and R10a as written, an independent recompute matches every
number in both runs, and the supplement only qualifies how the verdict reads. The row should not go higher than
reviewed. It is one run on one item set, one draw decides the qualifier, and the heads alone sit at the band boundary.
