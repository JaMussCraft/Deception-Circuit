# D2 premise readings

Generated 2026-11-02T21:19:53 by scripts/d2_premise.py read.

Refusal direction: chosen {'bypass': -9.814223289489746, 'degenerate': False, 'induce': 7.715332984924316, 'kl': 0.054618071764707565, 'layer': 11, 'norm': 4.234919548034668, 'position': -5}, valid True, harmful refusal share 1.0 unablated and 0.0 ablated.

| task | gate AUROC | rate D | rate I | rate H | gap | interval | ablated gap | separates | refusal explains | R2 reading |
|---|---|---|---|---|---|---|---|---|---|---|
| far_v2 | 1.000 | 1.000 | 0.995 | 0.000 | 0.005 | 0.000 to 0.018 | 0.000 | False | True | I patterns like D: falsity state |
| sdr_v2 | 1.000 | 1.000 | 0.840 | 0.000 | 0.160 | 0.086 to 0.227 | 0.136 | True | False | I patterns like D: falsity state |
| ser_v2 | 1.000 | 1.000 | 0.855 | 0.000 | 0.145 | 0.076 to 0.215 | 0.032 | False | True | I patterns like D: falsity state |

Acts-on-it arm:

- far_v2: maintenance D 0.010, I 0.024, H 0.005; gap -0.012; ablated gap -0.067; separates False; refusal explains True; proxy agreement 0.988; undefined (D and H within 0.30).
- sdr_v2: maintenance D 0.039, I 0.004, H 0.000; gap 0.031; ablated gap 0.030; separates False; refusal explains False; proxy agreement 0.987; undefined (D and H within 0.30).
- ser_v2: maintenance D 0.005, I 0.004, H 0.000; gap 0.000; ablated gap 0.014; separates False; refusal explains True; proxy agreement 0.997; undefined (D and H within 0.30).

Judge checks (R11):

- crosscheck: 200 rows compared, agreement 0.965, agreement without UNCLEAR 1.000.
- rejudge: 213 rows compared, agreement 1.000, agreement without UNCLEAR 1.000; flip rate 0.000.

Verdict: premise passes on ['sdr_v2']; final True.
