# Pilot round 7

| cell | task | family | suffix | SER | n | inversion | identity | survivors | HI acc | HI item_2 | GPU-h | cap | status | reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| r7_far_rule_demo_fiction_off | far_v2 | rule_instructed | off | - | 1000 | 0.6% | 0.8% | 7 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0.005882 < 0.02; identity contingent rate 0.008163 < 0.02; projected full-build cost inf GPU-h > 5 |
| r7_far_rule_demo_off | far_v2 | rule_instructed | off | - | 1000 | 1.6% | 1.6% | 16 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0.01569 < 0.02; identity contingent rate 0.01633 < 0.02; projected full-build cost inf GPU-h > 5 |
| r7_far_rule_demo_on | far_v2 | rule_instructed | on | - | 1000 | 8.6% | 2.2% | 55 | 0.991 | 0.491 | inf | 0.15 | fail | projected full-build cost inf GPU-h > 5 |
| r7_far_strong_off | far_v2 | rule_instructed | off | - | 1000 | 4.1% | 0.4% | 23 | 1 | 0.5 | inf | 0.15 | fail | identity contingent rate 0.004082 < 0.02; projected full-build cost inf GPU-h > 5 |
| r7_far_strong_on | far_v2 | rule_instructed | on | - | 1000 | 8.8% | 1.0% | 50 | 1 | 0.5 | inf | 0.15 | fail | identity contingent rate 0.0102 < 0.02; projected full-build cost inf GPU-h > 5 |
| r7_sdr_rule_demo_on | sdr_v2 | rule_instructed | on | - | 1000 | 0.0% | 0.0% | 0 | - | - | inf | 0.15 | fail | inversion contingent rate 0 < 0.02; identity contingent rate 0 < 0.02; projected full-build cost inf GPU-h > 5; honest-instruction item_2 share n/a outside [0.35, 0.65]; honest-instruction accuracy n/a < 0.8 |
| r7_ser_rule_demo_on_B | ser_v2 | rule_instructed | on | B | 1000 | 0.0% | 0.6% | 3 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0 < 0.02; identity contingent rate 0.006122 < 0.02; projected full-build cost inf GPU-h > 5 |

All tasks pass under one suffix policy within budget: **False**
Best passing cell per task: {'far_v2': None, 'sdr_v2': None, 'ser_v2': None}
Pair-driven collapse (top-5 pairs > 50% of survivors): ['r7_far_rule_demo_fiction_off', 'r7_far_rule_demo_off', 'r7_ser_rule_demo_on_B']
