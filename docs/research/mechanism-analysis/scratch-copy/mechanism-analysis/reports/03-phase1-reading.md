# Ticket 03 phase-1 reading (impl-03, 2026-10-25)

Tables: `reports/03-1a-results.md`, `03-1b-results.md`, `03-1c-results.md` (+ `.json`), built by
`outputs/_launch_mechanism_analysis/p1{a,b,c}_results.py`; curated copies under `docs/research/mechanism-analysis/phase1a/`
and `phase1/`. Held-out sample n = 100, seed 1, the selection ids excluded.

## Verdict

**R-AB overall: A′ (far A′, ser A′, sdr B).** Small sets mediate the pressure on far and ser, but they also carry the
item. Those sets lie mostly outside the six circuits. R-inv labels every deciding set "instructed inversion machinery",
not deception-specific. No phase-1 test finds deception-specific machinery inside the circuits.

## R-AB per task (held-out D, neutral twin, post-clause)

| task | reading | deciding set | f_D [95% CI] | KO acc | null f max | (ii) H / F acc drop | members outside U |
| --- | --- | --- | --- | --- | --- | --- | --- |
| far | A′ | greedy k = 20 | 0.893 [0.860, 0.927] | 0.000 | 0.309 | 0.31 / 0.33 | 15 of 20 |
| sdr | B | single k = 20 (descriptive) | 0.485 [0.440, 0.533] | 0.560 | 0.434 | 0.98 / 1.00 | 9 of 20 |
| ser | A′ | greedy k = 20 | 0.904 [0.859, 0.951] | 0.050 | 0.369 | 0.25 / 0.18 | 12 of 20 |

- No k <= 20 passes (i) with the single selector on any task. Greedy passes (i) only at k = 20 on far and ser.
- far's greedy k = 10 passes (ii) (H/F margins move by 9%) but misses (i) (f 0.676). ser's greedy k = 10 just misses
  (f 0.746).
- sdr B: the best k <= 20 is greedy k = 20 (f 0.664, KO acc 0.36). The shared-class share of the positive top-80 S2p
  effect is 0.554.
- A′ is settled only by the phase-3 adjudication. Routing share (c) is <= 0.25 on both A′ tasks (far 0.163, ser 0.006),
  so an A′-mover or A′-unresolved call would be claimable there.
- Caveat: an MLP's layer-matched null is the MLP itself (one block per layer). For all-MLP candidates (sdr k = 1, 2)
  the null equals S_k and (i) cannot pass. No reading depends on those k.

## R-inv (paired; R23 option B primary, R19(3) subset as robustness)

| task | rows | n | f_D | f_I | f_I - 0.5 f_D [95% CI] | label |
| --- | --- | --- | --- | --- | --- | --- |
| far | option B | 100 | 0.866 | 0.798 | 0.365 [0.332, 0.393] | instructed inversion (polarity-confounded) |
| far | inversion-polarity only | 83 | 0.847 | 0.775 | 0.352 [0.320, 0.385] | instructed inversion |
| far | R19(3) subset | 14 | 0.882 | 0.855 | 0.414 [0.353, 0.471] | instructed inversion |
| sdr | option B | 100 | 0.425 | 0.309 | 0.097 [0.024, 0.155] | instructed inversion |
| sdr | inversion-polarity only | 48 | 0.401 | 0.279 | 0.078 [0.002, 0.143] | instructed inversion |
| sdr | R19(3) subset | 73 | 0.478 | 0.288 | 0.049 [-0.018, 0.122] | undecided |
| ser | option B | 100 | 0.925 | 0.679 | 0.217 [0.165, 0.268] | instructed inversion |
| ser | inversion-polarity only | 48 | 0.880 | 0.661 | 0.221 [0.142, 0.295] | instructed inversion |
| ser | R19(3) subset | 26 | 0.877 | 0.674 | 0.236 [0.161, 0.322] | instructed inversion |

Both samples condition on survival of I's filter. FAR stays polarity-confounded, and its like-for-like
inversion-polarity row gives the same label. Per Component, the S7 (I) sweep matches S2p (D): most S2p top-20
Components are inversion-shared (far 20, sdr 18, ser 16).

## U-only arm (R24, descriptive)

The circuits' best heads mediate less than the model's best Components. No U-only k reaches (i) on any task. At
k = 20, U-only f_D is 0.405 (far), 0.407 (sdr) and 0.520 (ser). The unrestricted single selector gives 0.545, 0.485
and 0.663, and greedy gives 0.893, 0.664 and 0.904.

## Routing (shares of the clean-minus-twin gap, deciding set's preliminary C_t)

| task | (a) all 32 MLPs | (b) heads outside C_t | (c) all outside C_t |
| --- | --- | --- | --- |
| far | 0.248 | 0.232 | 0.163 |
| sdr | 0.364 | 0.224 | 0.297 |
| ser | 0.267 | 0.046 | 0.006 |

## Predictions

| prediction | outcome |
| --- | --- |
| R-A1: some set 3-6 is deception-specific | refuted (core = answer machinery, a positional collapse on far and ser; the rest partial or none) |
| RQ-A: core >= 2/3 shared | confirmed on sdr (25/31), refuted on far (16/31) and ser (18/31) |
| RQ-A: exclusives majority deception-leaning | refuted (3/8, 0/14, 1/10) |
| Positive control behaves as in v1 | confirmed |
| C-own | refuted on every task (far 7/8, Holm p 0.105) |
| C-MLP | refuted (mlp.11, 13, 16 deception-leaning on ser alone) |
| C-v1 | refuted (0 of 4) |
| C-confound: far's D-H effect survives without the core | refuted, so the paper says far's D-H effect was core (set 5 interchange 0.191 vs set 6 0.476; held-out (D-H)-core f_D 0.105) |
| R-lens (exploratory): FAR honest-first rate exceeds act-naming by >= 0.2 | refuted (-0.02, 0.00) |
| R-AB | A′ overall (far A′, ser A′, sdr B) |
| R-inv | instructed inversion machinery (far, ser; sdr on option B, undecided on the R19(3) subset) |

**Exclusive-head identities (R5, ticket 07):** no headline claim rests on them. R-own and C-v1 fail, and the deciding sets hold
few exclusive heads (far: head.9.19 excl_far, head.15.8 excl_ser; ser: head.11.24 excl_far). C-reads is not part of
ticket 03.

## Proposed for C_t and U (phase 3)

- Deciding sets: far greedy k = 20, ser greedy k = 20 (A′, for adjudication); sdr single k = 20 (B, descriptive).
- MLP blocks per task's preliminary C_t (at most 10):
  - far: 4, 6, 7, 8, 9, 11, 13, 14, 15, 16
  - sdr: 4, 6, 7, 8, 12, 13, 14, 15, 16, 19
  - ser: 1, 5, 6, 7, 11, 13, 14, 15, 16, 19
  - common to all three: 6, 7, 13, 14, 15, 16
