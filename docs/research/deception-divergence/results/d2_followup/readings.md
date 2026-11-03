# D2 follow-up readings

Generated 2026-11-03T00:49:08 by scripts/d2_followup.py read (pre-registered sample: yes).

The D2 premise verdict (hand-back 07, readings_final) and finding F8 stand whatever this follow-up returns; its act-form gap under C_HI is a different reading from review 04's under C_H.

Drift anchor: maximum absolute feature difference 0.0000 against the bar 0.25 logits.

Direction label: (b). D and I share what C_HI reads (instructed falsity or instruction content).

## Act-form reading under C_HI

| task | role | gate AUROC | label | n | clusters | rate D | rate I | rate HI | gap | interval | spread | p_I | LOCO min | ablated gap | ablated AUROC | IH interaction | interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| far_v2 | primary | 1.000 | (b) | 210 | 12 | 1.000 | 0.990 | 0.000 | 0.010 | [0.000, 0.028] | 1.000 | 0.990 | 0.005 | 0.010 | 1.000 | 3.853 | [1.823, 6.205] |
| sdr_v2 | secondary | 0.999 | (b) | 35 | 7 | 1.000 | 0.886 | 0.000 | 0.114 | [0.000, 0.250] | 1.000 | 0.886 | 0.037 | 0.057 | 1.000 | 0.716 | [-1.449, 3.473] |
| ser_v2 | excluded | 0.976 | (b) | 1 | | | | | | | | | | | | | |

## Joint DT and HT reading (all test ids)

| task | spread | p_I | p_H | p_DT | p_HT | p_DT minus p_HT | interval | cell |
|---|---|---|---|---|---|---|---|---|
| far_v2 | 1.000 | 0.990 | 0.000 | 1.000 | 0.000 | 1.000 | [1.000, 1.000] | instruction content |
| sdr_v2 | 0.956 | 0.644 | -0.021 | 1.004 | 0.163 | 0.841 | [0.725, 0.940] | instruction content |
| ser_v2 | 0.823 | 0.356 | -0.107 | 0.961 | 0.190 | 0.771 | [0.647, 0.887] | instruction content |

## Descriptive

| task | gap all ids | interval | act | predicate | other | rate H under C_HI | frozen C_H rates HI, DT, HT, IH |
|---|---|---|---|---|---|---|---|
| far_v2 | 0.010 | [0.000, 0.028] | 0.010 | n/a | n/a | 0.000 | [0.005, 1.000, 0.000, 0.010] |
| sdr_v2 | 0.340 | [0.242, 0.442] | 0.114 | 0.386 | 0.347 | 0.000 | [0.240, 1.000, 0.692, 0.286] |
| ser_v2 | 0.530 | [0.374, 0.693] | 0.000 | 0.426 | 0.690 | 0.032 | [0.956, 1.000, 0.936, n/a] |
