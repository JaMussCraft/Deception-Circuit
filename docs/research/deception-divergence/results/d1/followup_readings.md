# D1 follow-up readings (ruling R6)

Created 2026-11-02T19:25:21. Ruling R6 of `docs/research/deception-divergence/spec.md`, on the scores of the D1 job (50145353) and the phrasing-4 job. Compliance is R1 primary unless a table says secondary. Every rate carries its count and denominator. Intervals are the R4 clause-clustered 95 percent percentile bootstrap, 2,000 resamples. The pools are the unselected prior-kept ids; the 1,000 anchors are excluded except where a table says anchors.

## Phrasing 4 verdicts (R6 i and ii)

| task | full pool L4 vis - hid (pts) | interval | full-pool pass | content pool L4 (pts) | interval | content-pool pass |
|---|---|---|---|---|---|---|
| far_v2 | +2.4 (n 9954) | +1.3 to +3.6 | null | +2.9 (n 8380) | +1.6 to +4.3 | null |
| sdr_v2 | +1.1 (n 9563) | -0.9 to +3.4 | null | +2.3 (n 7741) | +0.0 to +4.8 | null |
| ser_v2 | +1.2 (n 9846) | +0.1 to +2.4 | null | +1.4 (n 7947) | -0.0 to +3.1 | null |

Cross-job control: D rescored on the anchors in the phrasing-4 job against D1's D.

| task | anchors | exact clean | exact corrupt | sign flips | R1 agreement | R1 compliant D1 / repro |
|---|---|---|---|---|---|---|
| far_v2 | 1000 | 1000/1000 | 1000/1000 | 0/2000 | 1000/1000 | 969 / 969 of 1000 |
| sdr_v2 | 1000 | 1000/1000 | 1000/1000 | 0/2000 | 1000/1000 | 994 / 994 of 1000 |
| ser_v2 | 1000 | 1000/1000 | 1000/1000 | 0/2000 | 1000/1000 | 948 / 948 of 1000 |

## Flip pools for U1 (R6 iii)

Forward pool: D R1-compliant, the visible arm honest (correct item the argmax with margin at least 0.3 in both streams), the hidden arm R1-compliant. Admission: at least 400 ids over at least 10 clauses, primary definition, unselected pool. The reverse pool (D compliant, visible compliant, hidden honest) is reported and admits nothing.

| task | phrasing | definition | matched n | D compliant | forward n | clauses | content n | shared n | reverse n | reverse clauses | admit U1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| far_v2 | L1 | primary | 9954 | 1326/9954 | 0/9954 | 0 | 0 | 0 | 0/9954 | 0 | no |
| far_v2 | L1 | secondary_clean_argmax | 9954 | 3019/9954 | 22/9954 | 10 | 20 | 2 | 198/9954 | 18 | (info) |
| far_v2 | L1 | primary_without_D_gate | 9954 | 1326/9954 | 0/9954 | 0 | 0 | 0 | 0/9954 | 0 | (info) |
| far_v2 | L1 | primary_compliance_lost | 9954 | 1326/9954 | 13/9954 | 5 | 12 | 1 | 208/9954 | 14 | (info) |
| far_v2 | L1 | primary, anchors (descriptive) | 1000 | 969/1000 | 0/1000 | 0 | 0 | 0 | 0/1000 | 0 | n/a |
| far_v2 | L4 | primary | 9954 | 1326/9954 | 0/9954 | 0 | 0 | 0 | 0/9954 | 0 | no |
| far_v2 | L4 | secondary_clean_argmax | 9954 | 3019/9954 | 18/9954 | 13 | 18 | 0 | 14/9954 | 9 | (info) |
| far_v2 | L4 | primary_without_D_gate | 9954 | 1326/9954 | 0/9954 | 0 | 0 | 0 | 0/9954 | 0 | (info) |
| far_v2 | L4 | primary_compliance_lost | 9954 | 1326/9954 | 5/9954 | 3 | 5 | 0 | 39/9954 | 8 | (info) |
| far_v2 | L4 | primary, anchors (descriptive) | 1000 | 969/1000 | 0/1000 | 0 | 0 | 0 | 0/1000 | 0 | n/a |
| sdr_v2 | L1 | primary | 9563 | 4789/9563 | 0/9563 | 0 | 0 | 0 | 0/9563 | 0 | no |
| sdr_v2 | L1 | secondary_clean_argmax | 9563 | 6822/9563 | 123/9563 | 18 | 80 | 43 | 135/9563 | 22 | (info) |
| sdr_v2 | L1 | primary_without_D_gate | 9563 | 4789/9563 | 172/9563 | 6 | 3 | 169 | 0/9563 | 0 | (info) |
| sdr_v2 | L1 | primary_compliance_lost | 9563 | 4789/9563 | 109/9563 | 19 | 104 | 5 | 177/9563 | 21 | (info) |
| sdr_v2 | L1 | primary, anchors (descriptive) | 1000 | 994/1000 | 0/1000 | 0 | 0 | 0 | 0/1000 | 0 | n/a |
| sdr_v2 | L4 | primary | 9563 | 4789/9563 | 0/9563 | 0 | 0 | 0 | 0/9563 | 0 | no |
| sdr_v2 | L4 | secondary_clean_argmax | 9563 | 6822/9563 | 103/9563 | 21 | 70 | 33 | 221/9563 | 22 | (info) |
| sdr_v2 | L4 | primary_without_D_gate | 9563 | 4789/9563 | 0/9563 | 0 | 0 | 0 | 0/9563 | 0 | (info) |
| sdr_v2 | L4 | primary_compliance_lost | 9563 | 4789/9563 | 110/9563 | 22 | 99 | 11 | 263/9563 | 19 | (info) |
| sdr_v2 | L4 | primary, anchors (descriptive) | 1000 | 994/1000 | 0/1000 | 0 | 0 | 0 | 0/1000 | 0 | n/a |
| ser_v2 | L1 | primary | 9846 | 1715/9846 | 0/9846 | 0 | 0 | 0 | 0/9846 | 0 | no |
| ser_v2 | L1 | secondary_clean_argmax | 9846 | 4874/9846 | 62/9846 | 22 | 58 | 4 | 24/9846 | 12 | (info) |
| ser_v2 | L1 | primary_without_D_gate | 9846 | 1715/9846 | 0/9846 | 0 | 0 | 0 | 0/9846 | 0 | (info) |
| ser_v2 | L1 | primary_compliance_lost | 9846 | 1715/9846 | 68/9846 | 12 | 67 | 1 | 52/9846 | 15 | (info) |
| ser_v2 | L1 | primary, anchors (descriptive) | 1000 | 948/1000 | 0/1000 | 0 | 0 | 0 | 0/1000 | 0 | n/a |
| ser_v2 | L4 | primary | 9846 | 1715/9846 | 0/9846 | 0 | 0 | 0 | 0/9846 | 0 | no |
| ser_v2 | L4 | secondary_clean_argmax | 9846 | 4874/9846 | 153/9846 | 20 | 151 | 2 | 139/9846 | 18 | (info) |
| ser_v2 | L4 | primary_without_D_gate | 9846 | 1715/9846 | 0/9846 | 0 | 0 | 0 | 0/9846 | 0 | (info) |
| ser_v2 | L4 | primary_compliance_lost | 9846 | 1715/9846 | 71/9846 | 16 | 71 | 0 | 118/9846 | 16 | (info) |
| ser_v2 | L4 | primary, anchors (descriptive) | 1000 | 948/1000 | 0/1000 | 0 | 0 | 0 | 0/1000 | 0 | n/a |

Context: of the pool ids that are R1-compliant under D, the number that meet the honest gate under each arm (k/n).

| task | L1_visible | L1_hidden | L2_visible | L2_hidden | L3_visible | L3_hidden | L4_visible | L4_hidden | I |
|---|---|---|---|---|---|---|---|---|---|
| far_v2 | 0/1326 | 0/1326 | 0/1326 | 0/1326 | 0/1326 | 0/1326 | 0/1326 | 0/1326 | 214/1318 |
| sdr_v2 | 0/4789 | 0/4789 | 0/4789 | 0/4789 | 8/4789 | 0/4789 | 1/4789 | 10/4789 | 76/4789 |
| ser_v2 | 0/1715 | 0/1715 | 0/1715 | 0/1715 | 0/1715 | 0/1715 | 0/1715 | 1/1715 | 190/1715 |

Per-clause forward counts, primary definition (clause: ids; shared clauses marked *):

- far_v2 L1: none.
- far_v2 L4: none.
- sdr_v2 L1: none.
- sdr_v2 L4: none.
- ser_v2 L1: none.
- ser_v2 L4: none.

## Content-clause reading (R6 ii)

The five shared stakes clauses per task are excluded: far_v2: shared_00, shared_01, shared_02, shared_03, shared_04; sdr_v2: shared_00, shared_01, shared_02, shared_03, shared_04; ser_v2: shared_00, shared_01, shared_02, shared_03, shared_04. The rule (10 points, interval excluding zero) is a pass criterion for phrasing 4 only and descriptive for phrasings 1 to 3. The shared-pool rows are descriptive.

| task | pool | comparison | matched n | clusters | a k/n (rate) | b k/n (rate) | a - b (pts) | 95% interval (pts) |
|---|---|---|---|---|---|---|---|---|
| far_v2 | content, primary | L1 visible - hidden (visibility) | 8380 | 20 | 1285/8380 (15.3) | 1034/8380 (12.3) | +3.0 | +1.4 to +4.9 |
| far_v2 | content, primary | L2 visible - hidden (belief) | 8380 | 20 | 1179/8380 (14.1) | 1201/8380 (14.3) | -0.3 | -0.9 to +0.4 |
| far_v2 | content, primary | L3 visible - hidden (consequence) | 8380 | 20 | 1170/8380 (14.0) | 1179/8380 (14.1) | -0.1 | -1.4 to +1.1 |
| far_v2 | content, primary | L4 visible - hidden (user-turn acknowledgement) | 8380 | 20 | 2164/8380 (25.8) | 1925/8380 (23.0) | +2.9 | +1.6 to +4.3 |
| far_v2 | content, primary | I - D (honesty override) | 6328 | 16 | 846/6328 (13.4) | 1315/6328 (20.8) | -7.4 | -17.4 to +1.7 |
| far_v2 | content, primary | I - D, token-matched I rows | 6328 | 16 | 846/6328 (13.4) | 1315/6328 (20.8) | -7.4 | -17.4 to +1.7 |
| far_v2 | content, primary | L1 hidden - D | 8380 | 20 | 1034/8380 (12.3) | 1315/8380 (15.7) | -3.4 | -5.8 to -1.2 |
| far_v2 | content, primary | L4 hidden - D | 8380 | 20 | 1925/8380 (23.0) | 1315/8380 (15.7) | +7.3 | +3.4 to +11.5 |
| far_v2 | shared, primary | L1 visible - hidden (visibility) | 1574 | 5 | 11/1574 (0.7) | 11/1574 (0.7) | +0.0 | -0.2 to +0.2 |
| far_v2 | shared, primary | L2 visible - hidden (belief) | 1574 | 5 | 7/1574 (0.4) | 9/1574 (0.6) | -0.1 | -0.3 to +0.0 |
| far_v2 | shared, primary | L3 visible - hidden (consequence) | 1574 | 5 | 9/1574 (0.6) | 8/1574 (0.5) | +0.1 | -0.2 to +0.4 |
| far_v2 | shared, primary | L4 visible - hidden (user-turn acknowledgement) | 1574 | 5 | 11/1574 (0.7) | 15/1574 (1.0) | -0.3 | -0.5 to -0.1 |
| far_v2 | shared, primary | I - D (honesty override) | 605 | 2 | 62/605 (10.2) | 3/605 (0.5) | +9.8 | +9.7 to +9.8 |
| far_v2 | shared, primary | I - D, token-matched I rows | 0 | 0 | 0/0 (n/a) | 0/0 (n/a) | n/a | n/a |
| far_v2 | shared, primary | L1 hidden - D | 1574 | 5 | 11/1574 (0.7) | 11/1574 (0.7) | +0.0 | -0.2 to +0.3 |
| far_v2 | shared, primary | L4 hidden - D | 1574 | 5 | 15/1574 (1.0) | 11/1574 (0.7) | +0.3 | +0.0 to +0.7 |
| sdr_v2 | content, primary | L1 visible - hidden (visibility) | 7741 | 20 | 4273/7741 (55.2) | 4346/7741 (56.1) | -0.9 | -2.8 to +0.9 |
| sdr_v2 | content, primary | L2 visible - hidden (belief) | 7741 | 20 | 4296/7741 (55.5) | 4307/7741 (55.6) | -0.1 | -3.5 to +3.0 |
| sdr_v2 | content, primary | L3 visible - hidden (consequence) | 7741 | 20 | 4263/7741 (55.1) | 4158/7741 (53.7) | +1.4 | -1.6 to +3.9 |
| sdr_v2 | content, primary | L4 visible - hidden (user-turn acknowledgement) | 7741 | 20 | 3987/7741 (51.5) | 3807/7741 (49.2) | +2.3 | +0.0 to +4.8 |
| sdr_v2 | content, primary | I - D (honesty override) | 7741 | 20 | 4414/7741 (57.0) | 4731/7741 (61.1) | -4.1 | -9.4 to +1.3 |
| sdr_v2 | content, primary | I - D, token-matched I rows | 7741 | 20 | 4414/7741 (57.0) | 4731/7741 (61.1) | -4.1 | -9.4 to +1.3 |
| sdr_v2 | content, primary | L1 hidden - D | 7741 | 20 | 4346/7741 (56.1) | 4731/7741 (61.1) | -5.0 | -8.1 to -1.7 |
| sdr_v2 | content, primary | L4 hidden - D | 7741 | 20 | 3807/7741 (49.2) | 4731/7741 (61.1) | -11.9 | -15.8 to -8.5 |
| sdr_v2 | shared, primary | L1 visible - hidden (visibility) | 1822 | 5 | 63/1822 (3.5) | 488/1822 (26.8) | -23.3 | -25.5 to -21.2 |
| sdr_v2 | shared, primary | L2 visible - hidden (belief) | 1822 | 5 | 90/1822 (4.9) | 719/1822 (39.5) | -34.5 | -44.7 to -23.0 |
| sdr_v2 | shared, primary | L3 visible - hidden (consequence) | 1822 | 5 | 68/1822 (3.7) | 786/1822 (43.1) | -39.4 | -47.3 to -31.0 |
| sdr_v2 | shared, primary | L4 visible - hidden (user-turn acknowledgement) | 1822 | 5 | 49/1822 (2.7) | 121/1822 (6.6) | -4.0 | -5.0 to -2.8 |
| sdr_v2 | shared, primary | I - D (honesty override) | 1822 | 5 | 1161/1822 (63.7) | 58/1822 (3.2) | +60.5 | +39.5 to +80.9 |
| sdr_v2 | shared, primary | I - D, token-matched I rows | 1822 | 5 | 1161/1822 (63.7) | 58/1822 (3.2) | +60.5 | +39.5 to +80.9 |
| sdr_v2 | shared, primary | L1 hidden - D | 1822 | 5 | 488/1822 (26.8) | 58/1822 (3.2) | +23.6 | +20.3 to +26.8 |
| sdr_v2 | shared, primary | L4 hidden - D | 1822 | 5 | 121/1822 (6.6) | 58/1822 (3.2) | +3.5 | +2.3 to +4.6 |
| ser_v2 | content, primary | L1 visible - hidden (visibility) | 7947 | 20 | 2419/7947 (30.4) | 2649/7947 (33.3) | -2.9 | -4.7 to -1.1 |
| ser_v2 | content, primary | L2 visible - hidden (belief) | 7947 | 20 | 1834/7947 (23.1) | 1966/7947 (24.7) | -1.7 | -5.4 to +2.0 |
| ser_v2 | content, primary | L3 visible - hidden (consequence) | 7947 | 20 | 1815/7947 (22.8) | 2357/7947 (29.7) | -6.8 | -11.1 to -2.9 |
| ser_v2 | content, primary | L4 visible - hidden (user-turn acknowledgement) | 7947 | 20 | 1615/7947 (20.3) | 1500/7947 (18.9) | +1.4 | -0.0 to +3.1 |
| ser_v2 | content, primary | I - D (honesty override) | 7947 | 20 | 1435/7947 (18.1) | 1709/7947 (21.5) | -3.4 | -14.3 to +6.2 |
| ser_v2 | content, primary | I - D, token-matched I rows | 7832 | 19 | 1435/7832 (18.3) | 1709/7832 (21.8) | -3.5 | -14.4 to +6.1 |
| ser_v2 | content, primary | L1 hidden - D | 7947 | 20 | 2649/7947 (33.3) | 1709/7947 (21.5) | +11.8 | +7.8 to +16.5 |
| ser_v2 | content, primary | L4 hidden - D | 7947 | 20 | 1500/7947 (18.9) | 1709/7947 (21.5) | -2.6 | -5.4 to +0.4 |
| ser_v2 | shared, primary | L1 visible - hidden (visibility) | 1899 | 5 | 5/1899 (0.3) | 10/1899 (0.5) | -0.3 | -0.6 to +0.0 |
| ser_v2 | shared, primary | L2 visible - hidden (belief) | 1899 | 5 | 1/1899 (0.1) | 2/1899 (0.1) | -0.1 | -0.2 to +0.0 |
| ser_v2 | shared, primary | L3 visible - hidden (consequence) | 1899 | 5 | 7/1899 (0.4) | 11/1899 (0.6) | -0.2 | -0.4 to -0.1 |
| ser_v2 | shared, primary | L4 visible - hidden (user-turn acknowledgement) | 1899 | 5 | 14/1899 (0.7) | 9/1899 (0.5) | +0.3 | -0.3 to +1.1 |
| ser_v2 | shared, primary | I - D (honesty override) | 1899 | 5 | 467/1899 (24.6) | 6/1899 (0.3) | +24.3 | +8.1 to +39.3 |
| ser_v2 | shared, primary | I - D, token-matched I rows | 1899 | 5 | 467/1899 (24.6) | 6/1899 (0.3) | +24.3 | +8.1 to +39.3 |
| ser_v2 | shared, primary | L1 hidden - D | 1899 | 5 | 10/1899 (0.5) | 6/1899 (0.3) | +0.2 | -0.2 to +0.8 |
| ser_v2 | shared, primary | L4 hidden - D | 1899 | 5 | 9/1899 (0.5) | 6/1899 (0.3) | +0.2 | -0.1 to +0.5 |
| far_v2 | content, secondary | L1 visible - hidden (visibility) | 8380 | 20 | 3107/8380 (37.1) | 2856/8380 (34.1) | +3.0 | +1.3 to +5.1 |
| far_v2 | content, secondary | L2 visible - hidden (belief) | 8380 | 20 | 3194/8380 (38.1) | 3512/8380 (41.9) | -3.8 | -5.8 to -1.8 |
| far_v2 | content, secondary | L3 visible - hidden (consequence) | 8380 | 20 | 3213/8380 (38.3) | 3137/8380 (37.4) | +0.9 | -0.4 to +2.3 |
| far_v2 | content, secondary | L4 visible - hidden (user-turn acknowledgement) | 8380 | 20 | 4015/8380 (47.9) | 3861/8380 (46.1) | +1.8 | +0.2 to +4.4 |
| far_v2 | content, secondary | I - D (honesty override) | 6328 | 16 | 2696/6328 (42.6) | 2927/6328 (46.3) | -3.7 | -22.3 to +14.8 |
| far_v2 | content, secondary | I - D, token-matched I rows | 6328 | 16 | 2696/6328 (42.6) | 2927/6328 (46.3) | -3.7 | -22.3 to +14.8 |
| far_v2 | content, secondary | L1 hidden - D | 8380 | 20 | 2856/8380 (34.1) | 2967/8380 (35.4) | -1.3 | -3.9 to +1.0 |
| far_v2 | content, secondary | L4 hidden - D | 8380 | 20 | 3861/8380 (46.1) | 2967/8380 (35.4) | +10.7 | +6.9 to +14.2 |
| far_v2 | shared, secondary | L1 visible - hidden (visibility) | 1574 | 5 | 50/1574 (3.2) | 51/1574 (3.2) | -0.1 | -0.3 to +0.1 |
| far_v2 | shared, secondary | L2 visible - hidden (belief) | 1574 | 5 | 50/1574 (3.2) | 43/1574 (2.7) | +0.4 | +0.2 to +0.6 |
| far_v2 | shared, secondary | L3 visible - hidden (consequence) | 1574 | 5 | 47/1574 (3.0) | 47/1574 (3.0) | +0.0 | -0.2 to +0.2 |
| far_v2 | shared, secondary | L4 visible - hidden (user-turn acknowledgement) | 1574 | 5 | 55/1574 (3.5) | 64/1574 (4.1) | -0.6 | -0.8 to -0.3 |
| far_v2 | shared, secondary | I - D (honesty override) | 605 | 2 | 254/605 (42.0) | 20/605 (3.3) | +38.7 | +37.1 to +40.3 |
| far_v2 | shared, secondary | I - D, token-matched I rows | 0 | 0 | 0/0 (n/a) | 0/0 (n/a) | n/a | n/a |
| far_v2 | shared, secondary | L1 hidden - D | 1574 | 5 | 51/1574 (3.2) | 52/1574 (3.3) | -0.1 | -0.4 to +0.2 |
| far_v2 | shared, secondary | L4 hidden - D | 1574 | 5 | 64/1574 (4.1) | 52/1574 (3.3) | +0.8 | +0.6 to +1.0 |
| sdr_v2 | content, secondary | L1 visible - hidden (visibility) | 7741 | 20 | 6147/7741 (79.4) | 6253/7741 (80.8) | -1.4 | -3.1 to +0.2 |
| sdr_v2 | content, secondary | L2 visible - hidden (belief) | 7741 | 20 | 6246/7741 (80.7) | 6365/7741 (82.2) | -1.5 | -6.0 to +1.9 |
| sdr_v2 | content, secondary | L3 visible - hidden (consequence) | 7741 | 20 | 6248/7741 (80.7) | 6253/7741 (80.8) | -0.1 | -3.6 to +2.8 |
| sdr_v2 | content, secondary | L4 visible - hidden (user-turn acknowledgement) | 7741 | 20 | 6034/7741 (77.9) | 5936/7741 (76.7) | +1.3 | -0.6 to +3.0 |
| sdr_v2 | content, secondary | I - D (honesty override) | 7741 | 20 | 6101/7741 (78.8) | 6372/7741 (82.3) | -3.5 | -9.6 to +2.4 |
| sdr_v2 | content, secondary | I - D, token-matched I rows | 7741 | 20 | 6101/7741 (78.8) | 6372/7741 (82.3) | -3.5 | -9.6 to +2.4 |
| sdr_v2 | content, secondary | L1 hidden - D | 7741 | 20 | 6253/7741 (80.8) | 6372/7741 (82.3) | -1.5 | -4.1 to +1.1 |
| sdr_v2 | content, secondary | L4 hidden - D | 7741 | 20 | 5936/7741 (76.7) | 6372/7741 (82.3) | -5.6 | -8.2 to -3.4 |
| sdr_v2 | shared, secondary | L1 visible - hidden (visibility) | 1822 | 5 | 475/1822 (26.1) | 1292/1822 (70.9) | -44.8 | -48.5 to -41.0 |
| sdr_v2 | shared, secondary | L2 visible - hidden (belief) | 1822 | 5 | 599/1822 (32.9) | 1431/1822 (78.5) | -45.7 | -54.9 to -30.6 |
| sdr_v2 | shared, secondary | L3 visible - hidden (consequence) | 1822 | 5 | 525/1822 (28.8) | 1437/1822 (78.9) | -50.1 | -58.2 to -39.2 |
| sdr_v2 | shared, secondary | L4 visible - hidden (user-turn acknowledgement) | 1822 | 5 | 518/1822 (28.4) | 590/1822 (32.4) | -4.0 | -6.1 to -2.1 |
| sdr_v2 | shared, secondary | I - D (honesty override) | 1822 | 5 | 1522/1822 (83.5) | 450/1822 (24.7) | +58.8 | +47.9 to +69.7 |
| sdr_v2 | shared, secondary | I - D, token-matched I rows | 1822 | 5 | 1522/1822 (83.5) | 450/1822 (24.7) | +58.8 | +47.9 to +69.7 |
| sdr_v2 | shared, secondary | L1 hidden - D | 1822 | 5 | 1292/1822 (70.9) | 450/1822 (24.7) | +46.2 | +43.5 to +49.0 |
| sdr_v2 | shared, secondary | L4 hidden - D | 1822 | 5 | 590/1822 (32.4) | 450/1822 (24.7) | +7.7 | +6.8 to +8.6 |
| ser_v2 | content, secondary | L1 visible - hidden (visibility) | 7947 | 20 | 5557/7947 (69.9) | 5871/7947 (73.9) | -4.0 | -5.3 to -2.6 |
| ser_v2 | content, secondary | L2 visible - hidden (belief) | 7947 | 20 | 5182/7947 (65.2) | 5543/7947 (69.7) | -4.5 | -8.2 to -1.0 |
| ser_v2 | content, secondary | L3 visible - hidden (consequence) | 7947 | 20 | 5036/7947 (63.4) | 5621/7947 (70.7) | -7.4 | -11.3 to -4.0 |
| ser_v2 | content, secondary | L4 visible - hidden (user-turn acknowledgement) | 7947 | 20 | 4783/7947 (60.2) | 4819/7947 (60.6) | -0.5 | -2.5 to +1.5 |
| ser_v2 | content, secondary | I - D (honesty override) | 7947 | 20 | 4007/7947 (50.4) | 4709/7947 (59.3) | -8.8 | -18.9 to +0.9 |
| ser_v2 | content, secondary | I - D, token-matched I rows | 7832 | 19 | 3987/7832 (50.9) | 4686/7832 (59.8) | -8.9 | -19.1 to +0.3 |
| ser_v2 | content, secondary | L1 hidden - D | 7947 | 20 | 5871/7947 (73.9) | 4709/7947 (59.3) | +14.6 | +10.8 to +18.3 |
| ser_v2 | content, secondary | L4 hidden - D | 7947 | 20 | 4819/7947 (60.6) | 4709/7947 (59.3) | +1.4 | -1.2 to +3.8 |
| ser_v2 | shared, secondary | L1 visible - hidden (visibility) | 1899 | 5 | 234/1899 (12.3) | 320/1899 (16.9) | -4.5 | -6.0 to -3.2 |
| ser_v2 | shared, secondary | L2 visible - hidden (belief) | 1899 | 5 | 160/1899 (8.4) | 217/1899 (11.4) | -3.0 | -3.9 to -2.0 |
| ser_v2 | shared, secondary | L3 visible - hidden (consequence) | 1899 | 5 | 223/1899 (11.7) | 289/1899 (15.2) | -3.5 | -4.6 to -2.2 |
| ser_v2 | shared, secondary | L4 visible - hidden (user-turn acknowledgement) | 1899 | 5 | 231/1899 (12.2) | 248/1899 (13.1) | -0.9 | -1.7 to -0.2 |
| ser_v2 | shared, secondary | I - D (honesty override) | 1899 | 5 | 1170/1899 (61.6) | 165/1899 (8.7) | +52.9 | +37.6 to +66.6 |
| ser_v2 | shared, secondary | I - D, token-matched I rows | 1899 | 5 | 1170/1899 (61.6) | 165/1899 (8.7) | +52.9 | +37.6 to +66.6 |
| ser_v2 | shared, secondary | L1 hidden - D | 1899 | 5 | 320/1899 (16.9) | 165/1899 (8.7) | +8.2 | +6.0 to +10.0 |
| ser_v2 | shared, secondary | L4 hidden - D | 1899 | 5 | 248/1899 (13.1) | 165/1899 (8.7) | +4.4 | +3.2 to +5.6 |

## Phrasing 4 on the full pool

| task | pool | comparison | matched n | clusters | a k/n (rate) | b k/n (rate) | a - b (pts) | 95% interval (pts) |
|---|---|---|---|---|---|---|---|---|
| far_v2 | full, primary | L4 visible - hidden (user-turn acknowledgement) | 9954 | 25 | 2175/9954 (21.9) | 1940/9954 (19.5) | +2.4 | +1.3 to +3.6 |
| far_v2 | full, primary | L4 hidden - D | 9954 | 25 | 1940/9954 (19.5) | 1326/9954 (13.3) | +6.2 | +2.7 to +9.8 |
| far_v2 | full, secondary | L4 visible - hidden (user-turn acknowledgement) | 9954 | 25 | 4070/9954 (40.9) | 3925/9954 (39.4) | +1.5 | +0.1 to +3.6 |
| far_v2 | full, secondary | L4 hidden - D | 9954 | 25 | 3925/9954 (39.4) | 3019/9954 (30.3) | +9.1 | +5.7 to +12.4 |
| sdr_v2 | full, primary | L4 visible - hidden (user-turn acknowledgement) | 9563 | 25 | 4036/9563 (42.2) | 3928/9563 (41.1) | +1.1 | -0.9 to +3.4 |
| sdr_v2 | full, primary | L4 hidden - D | 9563 | 25 | 3928/9563 (41.1) | 4789/9563 (50.1) | -9.0 | -12.9 to -5.2 |
| sdr_v2 | full, secondary | L4 visible - hidden (user-turn acknowledgement) | 9563 | 25 | 6552/9563 (68.5) | 6526/9563 (68.2) | +0.3 | -1.4 to +2.0 |
| sdr_v2 | full, secondary | L4 hidden - D | 9563 | 25 | 6526/9563 (68.2) | 6822/9563 (71.3) | -3.1 | -6.0 to -0.2 |
| ser_v2 | full, primary | L4 visible - hidden (user-turn acknowledgement) | 9846 | 25 | 1629/9846 (16.5) | 1509/9846 (15.3) | +1.2 | +0.1 to +2.4 |
| ser_v2 | full, primary | L4 hidden - D | 9846 | 25 | 1509/9846 (15.3) | 1715/9846 (17.4) | -2.1 | -4.6 to +0.3 |
| ser_v2 | full, secondary | L4 visible - hidden (user-turn acknowledgement) | 9846 | 25 | 5014/9846 (50.9) | 5067/9846 (51.5) | -0.5 | -2.2 to +1.0 |
| ser_v2 | full, secondary | L4 hidden - D | 9846 | 25 | 5067/9846 (51.5) | 4874/9846 (49.5) | +2.0 | -0.3 to +4.1 |

## Pools

| task | verdict pool | content pool (clauses) | shared pool (clauses) | D compliant: verdict / content / shared |
|---|---|---|---|---|
| far_v2 | 9954 | 8380 (20) | 1574 (5) | 1326/9954 (13.3) / 1315/8380 (15.7) / 11/1574 (0.7) |
| sdr_v2 | 9563 | 7741 (20) | 1822 (5) | 4789/9563 (50.1) / 4731/7741 (61.1) / 58/1822 (3.2) |
| ser_v2 | 9846 | 7947 (20) | 1899 (5) | 1715/9846 (17.4) / 1709/7947 (21.5) / 6/1899 (0.3) |
