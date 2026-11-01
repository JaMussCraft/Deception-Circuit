# V3 heldout numerical comparison

All masks were frozen before these outcomes. Native semantic labels are pending. Exact SDR/WT full-vocabulary identity controls and all64 native generation identity controls passed.

| Mask | Heads | SDR surrogate reduction | D-label argmax /64 | H correct /64 | H lost / gained | WT PPL increase |
|---|---:|---:|---:|---:|---:|---:|
| intact | 0 | 0.00% | 64 | 42 | 0 / 0 | -0.00% |
| oldD69 | 69 | 58.70% | 29 | 32 | 22 / 12 | 21.16% |
| oldW9 | 9 | 58.81% | 33 | 37 | 9 / 4 | 1.21% |
| new-W13 | 13 | 60.05% | 29 | 41 | 6 / 5 | 1.40% |
| new-allW28 | 28 | 65.33% | 21 | 42 | 3 / 3 | 5.11% |

W13 and all-W28 compare favorably to D69 on the trained surrogate and these collateral measurements. This is a comparison of particular masks under one matched intervention protocol; it does not establish general superiority of discovery algorithms or a deception-specific mechanism. W13 and D69 tie on D-label argmax count; D69 has lower mean deceptive-label probability (0.460 vs0.495), so the suppression ranking is metric-dependent. All-W28 improves both the surrogate and mean deceptive-label probability (0.390) relative to D69.

Probability mass under D prompts (deceptive / truthful / other):

- intact: 0.8214 / 0.1756 / 0.0030.
- oldD69: 0.4601 / 0.4544 / 0.0855.
- oldW9: 0.5040 / 0.4928 / 0.0032.
- new-W13: 0.4945 / 0.5019 / 0.0035.
- new-allW28: 0.3897 / 0.6043 / 0.0060.

All-W28 has unchanged net H correctness but loses3 previously correct cases and gains3 others; it does not preserve every honest response. Native deception, truthful correction and coherent refusal must be judged separately before making behavioral transfer claims. These small, fixed heldout slices and one training seed support exploratory comparisons.
