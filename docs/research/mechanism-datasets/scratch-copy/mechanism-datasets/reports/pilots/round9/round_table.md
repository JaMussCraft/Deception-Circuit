# Pilot round 9

| cell | task | family | suffix | SER | n | inversion | identity | survivors | HI acc | HI item_2 | GPU-h | cap | status | reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| r9_far_unified_on | far_v2 | rule_instructed | on | - | 1000 | 9.4% | 1.8% | 57 | 0.991 | 0.491 | inf | 0.15 | fail | identity contingent rate 0.01837 < 0.02; projected full-build cost inf GPU-h > 5 |
| r9_sdr_unified_on | sdr_v2 | rule_instructed | on | - | 1000 | 20.4% | 5.9% | 133 | 0.868 | 0.391 | 0.572 | 0.1 | pass | - |
| r9_ser_cr_unified_on_B | ser_v2 | rule_instructed | on | B | 1500 | 5.2% | 4.4% | 72 | 0.944 | 0.556 | 0.507 | 0.15 | pass | - |
| r9_ser_unified_on_B | ser_v2 | rule_instructed | on | B | 1500 | 4.6% | 4.8% | 70 | 0.943 | 0.557 | 0.686 | 0.15 | pass | - |

All tasks pass under one suffix policy within budget: **False**
Best passing cell per task: {'far_v2': None, 'sdr_v2': 'r9_sdr_unified_on', 'ser_v2': 'r9_ser_unified_on_B'}
