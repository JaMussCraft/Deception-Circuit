# Pilot round 8

| cell | task | family | suffix | SER | n | inversion | identity | survivors | HI acc | HI item_2 | GPU-h | cap | status | reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| r8_far_strong_demo_on | far_v2 | rule_instructed | on | - | 1000 | 13.9% | 8.8% | 114 | 0.991 | 0.5 | 0.435 | 0.1 | pass | - |
| r8_far_strong_off | far_v2 | rule_instructed | off | - | 1000 | 5.3% | 2.2% | 38 | 1 | 0.5 | 1.24 | 0.15 | pass | - |
| r8_far_strong_on | far_v2 | rule_instructed | on | - | 1000 | 11.6% | 2.4% | 71 | 1 | 0.5 | 1.43 | 0.15 | pass | - |
| r8_sdr_strong_on | sdr_v2 | rule_instructed | on | - | 1000 | 12.2% | 3.5% | 79 | 0.861 | 0.386 | 1.28 | 0.15 | pass | - |
| r8_ser_strong_on_B | ser_v2 | rule_instructed | on | B | 1000 | 2.5% | 1.6% | 21 | 0.952 | 0.548 | inf | 0.15 | fail | identity contingent rate 0.01633 < 0.02; projected full-build cost inf GPU-h > 5 |

All tasks pass under one suffix policy within budget: **False**
Best passing cell per task: {'far_v2': 'r8_far_strong_demo_on', 'sdr_v2': 'r8_sdr_strong_on', 'ser_v2': None}
Pair-driven collapse (top-5 pairs > 50% of survivors): ['r8_far_strong_off', 'r8_ser_strong_on_B']
