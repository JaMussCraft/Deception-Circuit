# Closing the instructed deception route and testing it on spontaneous deception

Handoff page of the instructed-route direction (session claude-230e4716, Sun 1 Nov 2026). The starting prompt is
`START.md`, the frozen rules and the twelve rulings are in `spec.md`, the findings are rows F-rte-001 to F-rte-008 of
`docs/research/FINDINGS.md`, and every number below has an independent Opus review under `reviews/`.

## The question

The mechanism-analysis synthesis left a partial causal account of pressured deception on FAR and SER: clause readers
in layers 8 to 17 feed the query-side layer-17 quartet L17H24 to L17H27, which sets up late writers, with about 0.8 of
the twin gap reaching the output from components outside the analysed grid. This direction asked three things. B1:
is that outside share mediated by the quartet, and does the pressure enter the quartet at the option-token keys (Sun)
or at the final-token query (our path patching)? B2: does the model's falsity signal track literal falsity or
misleadingness, does the reported SDR wish run through the quartet, and do the SER deception-leaning MLPs replicate?
B3: does Llama-3.1-8B-Instruct show alignment faking, and does spontaneous deception use the instructed route?

## The verdict

**The route is real but not closed, and it is not deception-specific.** Every test ran under its frozen rule on
held-out data; nothing was selected on the test sample.

- **B1, bypass and query-side (F-rte-005, F-rte-006).** Restoring the quartet outputs removes 0.360 of the
  outside-grid share on FAR and 0.462 on SER, both under the 0.50 bar, so the loop does not close through the
  quartet alone: the deciding set reaches the same late writers by a parallel route that B1 does not name. The
  pressure enters at the final-token query on both tasks (query restoration moves 0.32 and 0.43 of the effect,
  key restoration at the option tokens about zero), replicating the synthesis selector reading and differing from
  Sun's key-side account and from SDR (F-sdr-012). The quartet is partly necessary everywhere, never sufficient.
- **B2, the signal is instructed inversion, not misleadingness (F-rte-004); the wish uses the quartet (F-rte-002);
  only mlp.13 replicates (F-rte-001).** A FAR falsity probe transfers to SER at AUROC 0.9999, but it scores the
  instructed inversion and honest-instruction cells almost as high, so under R2 it reads the instructed answer
  switch (the F-mech-003 confound) and cannot separate misleadingness from literal falsity. The quartet carries
  0.54 of the reported-wish effect on the 618 SDR ids against at most 0.03 for random layer-17 quartets. Of the
  three SER MLPs of F-mech-009, mlp.13 is deception-leaning in both held-out seeds and also leans on FAR; mlp.11
  and mlp.16 miss the factor-two bar.
- **B3, the premise failed; the sycophancy fallback finds a shared, non-specific route (F-rte-007, F-rte-008).**
  Under the public helpful-only prompt the judged monitored-minus-unmonitored compliance gap is 7.0 points
  (3.9 to 10.2) against the pre-registered 10, consistent in direction but a third of Mehta's 24.4, so B3 ran on
  sycophancy alone. Patching the union of the FAR and SER deciding sets and the quartet from the uncued twin over
  the post-cue span removes 0.724 (0.702 to 0.746) of the sycophancy cue effect, in the shared band, but the
  largest of 20 member-excluded null draws reaches 0.505, so the label is "shared, non-specific": a 32-head set
  with the same MLPs at random layer-matched heads does nearly as well. The quartet-query set S_q removes 0.331
  with a null maximum of 0.021. Sycophancy here is a cue-driven, non-instructed falsehood, not spontaneous
  deception, and every set also carries transparent inversion (F-mech-003).

Taken together with the specificity survey, the picture is the one the user expected: deception on this model reuses
ordinary cue-routing machinery. The quartet is a reusable selector that pressure, wish and sycophancy cues all reach
at the query; what decides deception against honest inversion is not in these sets.

## What to do next

- The named parallel route from the deciding set to mlp.30, mlp.31 and L31H0 is the open B1 question; a
  sender-resolved path patch from the deciding set to the three writers on the same 100 ids would reuse the B1
  batch files and the offline estimator of R9.
- The sycophancy null maximum of 0.505 says the shared band is reachable by random heads given the MLPs; a
  heads-only arm with its own null is in `outputs/_studies/b3/j4_syc_supplement` (job 23416459) and is reported,
  not deciding.
- Need N2 is open: a second alignment-faking elicitation (a different scaffold or a stronger model) is premise work
  under the 10-hour sub-cap and a new ruling; the fallback result stands either way.
- Discovery on the sycophancy contrast (plan B3 section 3.5) was not needed because f_syc(S_all) was not divergent.

## Pointers

- Plans: `plans/B1-plan.md`, `plans/B2-plan.md`, `plans/B3-plan.md`. Hand-backs 01 to 35 in `reports/` (35 is the J4 review hand-back).
- Reviews: `reviews/01-p3-review.md` (SER MLPs), `02-p2-review.md` (SDR wish), `03-j3-review.md` (positive
  control), `04-p1-review.md` (falsity probe), `05-b1-review.md` (loop closure), `06-b3-premise-review.md`,
  `07-j4-review.md` (sycophancy transfer).
- Results in the repository: `results/b1/b1_readings.{json,md}`, `results/p2/p2_wish.json`, `results/p3/p3_rcls.csv`.
- Raw outputs, git-ignored, in this worktree: `outputs/_analyses/instructed-route-b1/` and `-b2/`,
  `outputs/_studies/b3/` (premise, judge ledgers, j3, j4, parity).
- Code: `scripts/route_closure_readings.py`, `scripts/falsity_probe.py`, `scripts/b3_premise.py`,
  `scripts/b3_judge.py`, `scripts/b3_patch.py`, `spontaneous/` (patching, sets, judge, proxy, stats) and their
  tests under `tests/`.
- Budget: 13 reservations, 11.8 of 65 GPU-hours reserved and 4.4 used before the supplement (Delta
  beto-delta-gpu, Bridges-2 cis260361p); OpenRouter 2.38 of 20 dollars recorded, 2.22 settled. The ledger is
  `ledger.json`.
