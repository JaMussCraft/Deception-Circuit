# Pilot round 6

| cell | task | family | suffix | SER | n | inversion | identity | survivors | HI acc | HI item_2 | GPU-h | cap | status | reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| r6_far_qr_rule_fiction_off | far_v2 | rule_instructed | off | - | 1000 | 0.2% | 0.6% | 4 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0.001961 < 0.02; identity contingent rate 0.006122 < 0.02; projected full-build cost inf GPU-h > 5 |
| r6_far_rule_fiction_off | far_v2 | rule_instructed | off | - | 1000 | 0.8% | 0.2% | 5 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0.007843 < 0.02; identity contingent rate 0.002041 < 0.02; projected full-build cost inf GPU-h > 5 |
| r6_far_rule_fiction_on | far_v2 | rule_instructed | on | - | 1000 | 0.4% | 0.2% | 3 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0.003922 < 0.02; identity contingent rate 0.002041 < 0.02; projected full-build cost inf GPU-h > 5 |
| r6_far_rule_fiction_persona_off | far_v2 | rule_instructed | off | - | 1000 | 0.4% | 0.0% | 2 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0.003922 < 0.02; identity contingent rate 0 < 0.02; projected full-build cost inf GPU-h > 5 |
| r6_far_rule_persona_off | far_v2 | rule_instructed | off | - | 1000 | 0.6% | 0.2% | 4 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0.005882 < 0.02; identity contingent rate 0.002041 < 0.02; projected full-build cost inf GPU-h > 5 |
| r6_far_swap_rule_off | far_v2 | rule_instructed | off | - | 1000 | 1.0% | 0.0% | 5 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0.009804 < 0.02; identity contingent rate 0 < 0.02; projected full-build cost inf GPU-h > 5 |
| r6_far_swap_rule_persona_off | far_v2 | rule_instructed | off | - | 1000 | 0.8% | 0.2% | 5 | 1 | 0.5 | inf | 0.15 | fail | inversion contingent rate 0.007843 < 0.02; identity contingent rate 0.002041 < 0.02; projected full-build cost inf GPU-h > 5 |

All tasks pass under one suffix policy within budget: **False**
Best passing cell per task: {'far_v2': None}
Pair-driven collapse (top-5 pairs > 50% of survivors): ['r6_far_qr_rule_fiction_off', 'r6_far_rule_fiction_off', 'r6_far_rule_fiction_on', 'r6_far_rule_fiction_persona_off', 'r6_far_rule_persona_off', 'r6_far_swap_rule_off', 'r6_far_swap_rule_persona_off']
