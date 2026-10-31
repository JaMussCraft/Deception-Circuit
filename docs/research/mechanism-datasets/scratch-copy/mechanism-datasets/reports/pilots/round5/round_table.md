# Pilot round 5

| cell | task | family | suffix | SER | n | inversion | identity | survivors | HI acc | HI item_2 | GPU-h | cap | status | reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| r5_far_qr_rule_off | far_v2 | rule_instructed | off | - | 1000 | 0.6% | 0.0% | 3 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0.005882 < 0.02; identity contingent rate 0 < 0.02; projected full-build cost inf GPU-h > 5 |
| r5_far_rule_off | far_v2 | rule_instructed | off | - | 1000 | 0.2% | 0.0% | 1 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0.001961 < 0.02; identity contingent rate 0 < 0.02; projected full-build cost inf GPU-h > 5 |
| r5_far_rule_on | far_v2 | rule_instructed | on | - | 1000 | 0.0% | 0.0% | 0 | - | - | inf | 0.15 | fail | inversion contingent rate 0 < 0.02; identity contingent rate 0 < 0.02; projected full-build cost inf GPU-h > 5; honest-instruction item_2 share n/a outside [0.35, 0.65]; honest-instruction accuracy n/a < 0.8 |
| r5_sdr_rule_off | sdr_v2 | rule_instructed | off | - | 1000 | 5.9% | 1.0% | 35 | 0.857 | 0.529 | inf | 0.15 | fail | identity contingent rate 0.0102 < 0.02; projected full-build cost inf GPU-h > 5 |
| r5_sdr_rule_on | sdr_v2 | rule_instructed | on | - | 1000 | 18.8% | 9.4% | 142 | 0.891 | 0.433 | 0.341 | 0.1 | pass | - |
| r5_ser_cr_rule_off_B | ser_v2 | rule_instructed | off | B | 1000 | 7.5% | 6.3% | 69 | 0.986 | 0.514 | 0.732 | 0.1 | pass | - |
| r5_ser_rule_off_A | ser_v2 | rule_instructed | off | A | 1000 | 0.0% | 0.0% | 0 | - | - | inf | 0.15 | fail | inversion contingent rate 0 < 0.02; identity contingent rate 0 < 0.02; projected full-build cost inf GPU-h > 5; honest-instruction item_2 share n/a outside [0.35, 0.65]; honest-instruction accuracy n/a < 0.8 |
| r5_ser_rule_off_B | ser_v2 | rule_instructed | off | B | 1000 | 5.7% | 0.6% | 32 | 0.984 | 0.516 | inf | 0.15 | fail | identity contingent rate 0.006122 < 0.02; projected full-build cost inf GPU-h > 5 |
| r5_ser_rule_on_A | ser_v2 | rule_instructed | on | A | 1000 | 0.0% | 0.0% | 0 | - | - | inf | 0.15 | fail | inversion contingent rate 0 < 0.02; identity contingent rate 0 < 0.02; projected full-build cost inf GPU-h > 5; honest-instruction item_2 share n/a outside [0.35, 0.65]; honest-instruction accuracy n/a < 0.8 |
| r5_ser_rule_on_B | ser_v2 | rule_instructed | on | B | 1000 | 2.5% | 5.7% | 41 | 0.951 | 0.549 | 0.694 | 0.15 | pass | - |

All tasks pass under one suffix policy within budget: **False**
Best passing cell per task: {'far_v2': None, 'sdr_v2': 'r5_sdr_rule_on', 'ser_v2': 'r5_ser_cr_rule_off_B'}
Pair-driven collapse (top-5 pairs > 50% of survivors): ['r5_far_qr_rule_off', 'r5_far_rule_off', 'r5_ser_rule_on_B']
