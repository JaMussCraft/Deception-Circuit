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

The supplement run (heads_only, S_far, S_ser; job 23416459) had not finished when this review was written. Its section
below is pending.

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
- **The shared MLPs do not give a uniform offset.** All 20 draws contain mlp.5 to mlp.7, yet the draws range from
  −0.430 to 0.505 with a mean near zero. The MLPs are not lifting every draw toward 0.5. Whether they matter in
  combination with particular heads cannot be read from this run. The heads_only arm of the supplement is the direct
  test.
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
- The FAR- and SER-specific share is not separated by this run. S_far and S_ser in the supplement will bound it.

### 4. What the result licenses

The plan section 4 label applies: sycophancy is a cue-driven, non-instructed falsehood, not spontaneous deception. The
model may believe the user, and nothing in this task elicits a belief-contrary statement it knows to be false.

**What "shared, non-specific" licenses:**

- The union of the FAR and SER deciding sets and the quartet, patched from the cue through the Readout, carries most
  of a user cue's pull toward a wrong MMLU answer. That is 0.72 of the mean margin shift and 145 of 154 flips, with
  little collateral damage.
- The quartet that carries the instructed pressure on FAR and SER (F-rte-005, F-rte-006) also carries a third of this
  non-instructed cue's effect. Its null is tight: four random layer-17 heads reach at most 0.021.
- So the cue route these sets implement is not confined to operator instructions. It also serves a user's stated
  opinion.

**What it does not license:**

- **Deception-specific machinery.** F-mech-003 already shows the sets carry transparent inversion, and sycophancy is
  not deception.
- **That the FAR and SER members carry the effect.** The quartet and two Gupta writers inside S_all may carry much of
  it. The supplement's S_far and S_ser arms bound this.
- **That S_all is specific among sets of its size and layers.** One of 20 random 32-head draws with the same MLPs
  reaches 0.505 at post_tag. The label is pre-registered.
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

### 6. Supplement: heads_only, S_far and S_ser (pending)

Job 23416459 was in pass 2 (96 of 530 rows) when this review was written. Nothing in it is read here. How to read it
when it lands:

- **heads_only (S_all's 32 heads, heads-only null).**
  - If its f stays near 0.72, the three MLPs add little to S_all.
  - If its null maximum stays near 0.5, the width of the S_all null comes from patching 32 heads over the cue tokens,
    not from the shared MLPs.
  - A null maximum near 0.2 would put the width on the MLPs in combination with the heads.
- **S_far and S_ser.** Their f values, set against S_q's 0.331, bound how much of the transfer the FAR- and
  SER-specific members carry beyond the quartet and L15H8.

## Problems found

Severity-ordered. None changes the verdict.

1. **The non-specific label rests on one draw (medium, interpretation).** Draw 11 is 0.505 with interval 0.467 to
   0.541. The next draw is 0.442, and S_all exceeds every draw. The label is pre-registered and correct as applied,
   but the row should give the null maximum, its draw and how thin the crossing is, so the label is not read as "S_all
   is no better than random".
2. **The rule arm patches the cue tokens themselves (medium, interpretation).** post_tag starts on the 7 differing cue
   tokens, as R11 defines it. A large set of early-layer components interchanged there partly substitutes the cue's
   token content, which explains the wide null (SD 0.250 against 0.190 at the readout) and the large negative draws.
   No arm patches only the 23 shared positions after the cue window. That arm, by analogy with the "after the clause"
   arm of F-rte-002, would separate carrying the cue forward from reading the cue tokens. It is not required by R11.
   It would be a cheap follow-up: S_all and its 20 draws on 530 items is about 0.2 h on an A100, including the
   model load. Patching code for
   that span does not exist yet.
3. **Flip reversal is not a specificity measure for S_all (low, reporting).** Null draws with f near zero reverse 0.34
   to 0.43 of flips. Report reversal beside f with the non-flip damage (S_all 3 of 376; null draws 7 to 98), or not
   at all for S_all.
4. **The R11 verdict is not machine-written (low, bookkeeping).** `syc_results` computes the pass bar but no
   `transfer_verdict`, so the "shared, non-specific" label for J4 exists only in the orchestrator's reading. The
   readings file or the finding should state the rule number, the band, the null maximum and the label explicitly.
5. **results.json still loses the set-to-null-label mapping (low, carried over from review 03, problem 3).** The
   `nulls` summaries overwrite the label lists. `margins.json` keeps them, and `null_draws` and `null_kept_members`
   are now in both files, so the draws can be tied to labels by name.
6. **The supplement is pending (low, scope).** heads_only, S_far and S_ser are non-deciding under R11, so the verdict
   does not wait for them, but the MLP question and the FAR/SER-specific share do.

## Proposed finding text

Row F-rte-008, in the F-rte-002 shape:

> Does the instructed route carry a non-instructed, cue-driven falsehood (B3 transfer on sycophancy alone, R11):
> shared, non-specific; interchanging S_all (the FAR and SER deciding sets and the layer 17 quartet: 32 heads in
> layers 7 to 17 and mlp.5 to mlp.7) with its uncued-twin outputs from the cue's first differing token through the
> readout removes 0.724 (bootstrap 0.702 to 0.746; 0.669 to 0.770 clustered by 56 MMLU subjects) of the cue-induced
> shift of logit(cue letter) minus logit(gold) over the 530 of 800 MMLU items answered correctly without the cue, and
> reverses 145 of 154 cue-induced flips while 3 of 376 other kept items lose the right answer; it exceeds all 20
> layer-matched draws of 32 non-member heads with the same three MLPs, but the largest, 0.505 (draw 11, interval
> 0.467 to 0.541; next 0.442), reaches the 0.5 at which R5 labels the result non-specific; at the readout alone S_all
> removes 0.453 against a null maximum of 0.218; the quartet alone removes 0.331 at the post-cue positions (null
> maximum 0.021) and Gupta et al.'s six heads 0.486 (null maximum 0.180), and every flip either reverses S_all also
> reverses. Sycophancy here is a cue-driven, non-instructed falsehood, not spontaneous deception, and per F-mech-003
> the sets also carry transparent inversion, so "shared" means a shared cue route, not deception-specific machinery.
> Caveats: the non-specific label rests on one draw 0.005 over the bar; the post-cue span includes the 7 differing cue
> tokens, where random 32-head draws range from -0.430 to 0.505 (SD 0.250, against 0.190 at the readout), so flip
> reversal does not discriminate for this set (draws with f near zero reverse 0.34 to 0.43 of flips); S_all contains
> the quartet and two of Gupta's writers (L17H24, L15H8), so the share carried by the FAR and SER members alone is not
> separated, and the null draws share mlp.5 to mlp.7 under R10a; one prompt, one cue type and one neutral sentence,
> on MMLU only.

If the supplement lands before the row is written, add its numbers to the claim. Add the heads_only f with its
heads-only null maximum, and S_far and S_ser at post_tag with their null maxima, then trim the two caveats they
resolve.

Evidence:

- `outputs/_studies/b3/j4_syc/results.json`
- `outputs/_studies/b3/j4_syc/margins.json`
- `outputs/_studies/b3/j4_syc/run_manifest.json`
- `outputs/_studies/b3/parity/parity.json`
- `docs/research/instructed-route/reviews/07-j4-review.md`
- with the supplement: `outputs/_studies/b3/j4_syc_supplement/results.json` and its `run_manifest.json`

The commit is the run's, 21bc397.

**Strength.** "reviewed" is right. The run follows R11 and R10a as written, an independent recompute matches every
number, and the rule arm's verdict does not depend on the pending supplement. The row should not go higher than
reviewed: it is one run on one item set, with one draw deciding the qualifier.
