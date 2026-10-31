# Phase-3 results (ticket 05): path patching on C_t

Built by `outputs/_launch_mechanism_analysis/p3_results.py` from the cells `outputs/_analyses/mechanism-analysis-p3/{d,d_is}/Ct__leaf/<t>_v2` (Delta, fetched from Bridges-2). Path numbers are the normalized effect against the Neutral-Clause Twin unless a line says item swap: positive = the path helps the pressured (deceptive) answer. Floor 0.01 (docs/component-roles.md). Causal sample: n = 100 (the cells' sample.n_instances; the default causal sample, seed 0, which is R-AB's selection sample).

## A' adjudication (spec 2.3)

| task | R-AB | deciding set | heads / MLPs | q | kv_clause | kv_post_clause | kv_unresolved | none | call (> 50 % weight) | routing (c) | sub-reading | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| far | A' | greedy_k20 | 18 / 2 | 0.20 (3) | 0.74 (13) | 0.00 (0) | 0.03 (1) | 0.04 (1) | kv_clause | 0.163 | **A'-clause-reader** | pre-registered (R-AB reading A') |
| sdr | B | single_k20 | 14 / 6 | 0.64 (7) | 0.22 (4) | 0.00 (0) | 0.11 (2) | 0.03 (1) | q | 0.297 | **descriptive: q-dominated** | descriptive (R-AB reading B; S_20 of the single selector) |
| ser | A' | greedy_k20 | 19 / 1 | 0.03 (1) | 0.83 (14) | 0.10 (3) | 0.00 (0) | 0.03 (1) | kv_clause | 0.006 | **A'-clause-reader** | pre-registered (R-AB reading A') |

Shares are of the summed S2p single effect (phase-1 S2p mean drop) over the deciding set's heads; counts in brackets. MLP members are listed, never called. A task not read A′ gets no sub-reading (spec 2.3); its call is given as a descriptive shape.

### far: per head of the deciding set (pre-registered (R-AB reading A'))

MLP members (2): mlp.6.0, mlp.7.0. Negative S2p weights floored at 0: none.

| head | S2p weight | category | strongest path | support | SE | top Segment | Q n / abs | K+V n / abs | membership |
|---|---|---|---|---|---|---|---|---|---|
| head.9.29 | 1.082 | kv_clause | mlp.6.0->k.9.7 | 0.0529 | 0.0040 | pressure_clause | 2 / 0.036 | 8 / 0.280 | S_k |
| head.9.16 | 0.649 | q | mlp.8.0->q.9.16 | 0.0205 | 0.0017 | - | 2 / 0.033 | 2 / 0.026 | S_k |
| head.9.19 | 0.607 | q | mlp.8.0->q.9.19 | 0.0240 | 0.0031 | - | 1 / 0.024 | 2 / 0.026 | excl+DmH_minus_core+S_k |
| head.7.16 | 0.604 | kv_clause | mlp.6.0->k.7.4 | 0.0365 | 0.0029 | pressure_clause | 1 / 0.017 | 3 / 0.083 | S_k |
| head.11.0 | 0.597 | kv_clause | mlp.9.0->v.11.0 | 0.0455 | 0.0033 | pressure_clause | 1 / 0.016 | 12 / 0.288 | S_k |
| head.11.15 | 0.558 | kv_clause | mlp.9.0->v.11.3 | 0.0203 | 0.0021 | pressure_clause | 1 / 0.012 | 5 / 0.082 | S_k |
| head.10.22 | 0.459 | kv_clause | mlp.8.0->v.10.5 | 0.0389 | 0.0031 | pressure_clause | 0 / 0 | 8 / 0.140 | S_k |
| head.10.19 | 0.376 | kv_clause | mlp.9.0->v.10.4 | 0.0154 | 0.0020 | pressure_clause | 0 / 0 | 3 / 0.040 | S_k |
| head.10.25 | 0.376 | kv_clause | head.9.19->v.10.6 | 0.0454 | 0.0027 | pressure_clause | 2 / 0.025 | 15 / 0.315 | S_k |
| head.9.31 | 0.364 | kv_clause | mlp.6.0->k.9.7 | 0.0529 | 0.0040 | pressure_clause | 2 / 0.022 | 8 / 0.280 | DmH_minus_core+S_k |
| head.13.22 | 0.329 | kv_clause | mlp.9.0->k.13.5 | 0.1514 | 0.0063 | pressure_clause | 2 / 0.030 | 43 / 1.374 | S_k |
| head.10.29 | 0.322 | kv_clause | head.9.28->k.10.7 | 0.0164 | 0.0024 | pressure_clause | 3 / 0.033 | 2 / 0.028 | core+S_k |
| head.9.3 | 0.304 | q | mlp.8.0->q.9.3 | 0.0129 | 0.0016 | - | 1 / 0.013 | 0 / 0 | S_k |
| head.10.9 | 0.287 | kv_clause | mlp.9.0->k.10.2 | -0.0106 | 0.0018 | pressure_clause | 0 / 0 | 1 / 0.011 | S_k |
| head.11.27 | 0.280 | none | - | - | - | - | 0 / 0 | 0 / 0 | S_k |
| head.10.16 | 0.216 | kv_clause | mlp.9.0->v.10.4 | 0.0154 | 0.0020 | pressure_clause | 0 / 0 | 3 / 0.040 | S_k |
| head.15.8 | 0.207 | kv_unresolved | head.14.5->v.15.2 | 0.0497 | 0.0029 | unsegmented | 2 / 0.035 | 9 / 0.269 | S_k |
| head.13.23 | 0.192 | kv_clause | mlp.9.0->k.13.5 | 0.1514 | 0.0063 | pressure_clause | 1 / 0.014 | 43 / 1.374 | S_k |

### sdr: per head of the deciding set (descriptive (R-AB reading B; S_20 of the single selector))

MLP members (6): mlp.6.0, mlp.7.0, mlp.8.0, mlp.12.0, mlp.13.0, mlp.14.0. Negative S2p weights floored at 0: none.

| head | S2p weight | category | strongest path | support | SE | top Segment | Q n / abs | K+V n / abs | membership |
|---|---|---|---|---|---|---|---|---|---|
| head.14.5 | 0.873 | q | head.12.4->q.14.5 | 0.0455 | 0.0050 | - | 4 / 0.140 | 3 / 0.048 | core+S_k |
| head.14.4 | 0.690 | q | mlp.13.0->q.14.4 | 0.0755 | 0.0089 | - | 6 / 0.192 | 3 / 0.048 | core+S_k |
| head.12.4 | 0.479 | kv_clause | mlp.8.0->k.12.1 | 0.0480 | 0.0065 | pressure_clause | 2 / 0.046 | 13 / 0.304 | S_k |
| head.14.20 | 0.427 | q | head.13.18->q.14.20 | 0.0186 | 0.0022 | - | 4 / 0.057 | 2 / 0.025 | S_k |
| head.14.24 | 0.300 | q | mlp.12.0->q.14.24 | 0.0128 | 0.0018 | - | 2 / 0.023 | 0 / 0 | DmH_minus_core+S_k |
| head.15.11 | 0.281 | kv_unresolved | head.14.5->v.15.2 | 0.0875 | 0.0069 | unsegmented | 5 / 0.082 | 14 / 0.581 | S_k |
| head.13.18 | 0.261 | q | head.12.4->q.13.18 | 0.0176 | 0.0027 | - | 2 / 0.032 | 1 / 0.011 | core+S_k |
| head.15.8 | 0.250 | kv_unresolved | head.14.5->v.15.2 | 0.0875 | 0.0069 | unsegmented | 2 / 0.028 | 14 / 0.581 | S_k |
| head.13.23 | 0.219 | kv_clause | head.12.4->v.13.5 | 0.0732 | 0.0132 | pressure_clause | 0 / 0 | 11 / 0.290 | S_k |
| head.14.23 | 0.216 | q | mlp.13.0->q.14.23 | 0.0196 | 0.0022 | - | 2 / 0.036 | 2 / 0.025 | S_k |
| head.17.24 | 0.194 | q | head.14.4->q.17.24 | 0.2559 | 0.0130 | - | 12 / 1.003 | 1 / 0.011 | core+S_k |
| head.13.21 | 0.159 | kv_clause | head.12.4->v.13.5 | 0.0732 | 0.0132 | pressure_clause | 0 / 0 | 11 / 0.290 | core+S_k |
| head.11.1 | 0.154 | kv_clause | mlp.6.0->v.11.0 | 0.0108 | 0.0025 | pressure_clause | 0 / 0 | 2 / 0.021 | S_k |
| head.13.28 | 0.139 | none | - | - | - | - | 0 / 0 | 0 / 0 | S_k |

### ser: per head of the deciding set (pre-registered (R-AB reading A'))

MLP members (1): mlp.5.0. Negative S2p weights floored at 0: none.

| head | S2p weight | category | strongest path | support | SE | top Segment | Q n / abs | K+V n / abs | membership |
|---|---|---|---|---|---|---|---|---|---|
| head.11.0 | 1.206 | kv_clause | mlp.7.0->k.11.0 | 0.0759 | 0.0074 | pressure_clause | 2 / 0.053 | 21 / 0.570 | S_k |
| head.13.23 | 0.907 | kv_clause | mlp.11.0->k.13.5 | 0.1624 | 0.0112 | pressure_clause | 2 / 0.055 | 38 / 1.137 | S_k |
| head.9.29 | 0.905 | kv_clause | mlp.6.0->k.9.7 | 0.0899 | 0.0073 | pressure_clause | 1 / 0.014 | 16 / 0.449 | S_k |
| head.11.15 | 0.549 | kv_clause | head.9.28->k.11.3 | -0.0222 | 0.0033 | pressure_clause | 0 / 0 | 4 / 0.062 | S_k |
| head.8.15 | 0.341 | kv_post_clause | mlp.5.0->v.8.3 | -0.0241 | 0.0044 | question | 2 / 0.029 | 6 / 0.105 | S_k |
| head.13.22 | 0.338 | kv_clause | mlp.11.0->k.13.5 | 0.1624 | 0.0112 | pressure_clause | 1 / 0.015 | 38 / 1.137 | S_k |
| head.9.3 | 0.328 | kv_clause | mlp.7.0->v.9.0 | 0.0169 | 0.0043 | pressure_clause | 1 / 0.010 | 6 / 0.081 | S_k |
| head.14.24 | 0.323 | kv_clause | head.12.6->v.14.6 | 0.0334 | 0.0044 | pressure_clause | 1 / 0.014 | 6 / 0.101 | S_k |
| head.9.31 | 0.301 | kv_clause | mlp.6.0->k.9.7 | 0.0899 | 0.0073 | pressure_clause | 3 / 0.048 | 16 / 0.449 | S_k |
| head.13.21 | 0.276 | kv_clause | mlp.11.0->k.13.5 | 0.1624 | 0.0112 | pressure_clause | 1 / 0.012 | 38 / 1.137 | core+S_k |
| head.11.14 | 0.260 | kv_clause | head.9.28->k.11.3 | -0.0222 | 0.0033 | pressure_clause | 0 / 0 | 4 / 0.062 | S_k |
| head.8.24 | 0.239 | kv_post_clause | mlp.6.0->v.8.6 | 0.0350 | 0.0054 | question | 2 / 0.032 | 3 / 0.062 | S_k |
| head.13.6 | 0.235 | none | - | - | - | - | 0 / 0 | 0 / 0 | S_k |
| head.10.9 | 0.231 | kv_clause | mlp.6.0->v.10.2 | -0.0361 | 0.0045 | pressure_clause | 0 / 0 | 4 / 0.086 | S_k |
| head.11.24 | 0.222 | q | head.9.13->q.11.24 | -0.0176 | 0.0028 | - | 1 / 0.018 | 1 / 0.011 | S_k |
| head.7.14 | 0.221 | kv_clause | mlp.5.0->v.7.3 | 0.0911 | 0.0108 | pressure_clause | 0 / 0 | 4 / 0.200 | S_k |
| head.11.27 | 0.178 | kv_post_clause | head.9.30->v.11.6 | -0.0106 | 0.0012 | question | 0 / 0 | 1 / 0.011 | S_k |
| head.8.22 | 0.146 | kv_clause | mlp.7.0->v.8.5 | 0.0567 | 0.0065 | pressure_clause | 0 / 0 | 4 / 0.095 | S_k |
| head.9.13 | 0.140 | kv_clause | mlp.7.0->v.9.3 | 0.0108 | 0.0027 | pressure_clause | 0 / 0 | 1 / 0.011 | core+S_k |

### Robustness of the call (EXPLORATORY, not pre-registered)

The same cells re-read three ways: a head whose strongest path opposes the pressured answer counts as none; a head whose strongest path is under twice the floor (0.02) counts as none; each head placed by its larger Q or K+V total over the floor. K/V cells belong to a KV group, so the distinct groups behind the kv_clause heads are the independent tests.

| task | pre-registered call | positive path only | floor x2 | Q vs K+V totals | kv_clause heads / KV groups |
|---|---|---|---|---|---|
| far | kv_clause (kv_clause 0.74) | kv_clause (kv_clause 0.70) | kv_clause (kv_clause 0.58) | kv (kv 0.80) | 13 / 10 |
| sdr | q (q 0.64) | q (q 0.64) | mixed (q 0.38) | q (q 0.64) | 4 / 3 |
| ser | kv_clause (kv_clause 0.83) | kv_clause (kv_clause 0.69) | kv_clause (kv_clause 0.77) | kv (kv 0.94) | 14 / 10 |

## B-selector (spec 2.6)

- Clause 1, literal (one of L17H24-27 has category q on >= 2 tasks): **True**; q tasks per head: {'head.17.24': ['far', 'sdr', 'ser'], 'head.17.25': ['far', 'sdr', 'ser'], 'head.17.26': ['far', 'sdr', 'ser'], 'head.17.27': ['far', 'sdr', 'ser']}. Loose reading (some L17 head q, on >= 2 tasks): True (['far', 'sdr', 'ser']).
- Clause 2 (the core's L24 heads all kv_post_clause): on all tasks **False**; tasks where it holds: [].

| task | head | category | strongest path | support | SE | segment | Q n / signed / abs | K+V n / signed / abs | strongest K/V cell (mean) |
|---|---|---|---|---|---|---|---|---|---|
| far | head.17.24 | q | head.14.4->q.17.24 | 0.1535 | 0.0073 | - | 8 / 0.456 / 0.526 | 0 / 0 / 0 | mlp.13.0->k.17.6 (-0.0082) |
| far | head.17.25 | q | mlp.15.0->q.17.25 | 0.0311 | 0.0030 | - | 4 / 0.074 / 0.074 | 0 / 0 / 0 | mlp.13.0->k.17.6 (-0.0082) |
| far | head.17.26 | q | head.15.8->q.17.26 | 0.0349 | 0.0018 | - | 4 / 0.091 / 0.091 | 0 / 0 / 0 | mlp.13.0->k.17.6 (-0.0082) |
| far | head.17.27 | q | head.15.8->q.17.27 | 0.0424 | 0.0018 | - | 3 / 0.082 / 0.082 | 0 / 0 / 0 | mlp.13.0->k.17.6 (-0.0082) |
| far | head.24.17 | none | - | - | - | - | 0 / 0 / 0 | 0 / 0 / 0 | mlp.9.0->v.24.4 (-0.0007) |
| far | head.24.20 | none | - | - | - | - | 0 / 0 / 0 | 0 / 0 / 0 | head.10.16->k.24.5 (-0.0008) |
| far | head.24.26 | q | head.17.24->q.24.26 | 0.0165 | 0.0006 | - | 2 / 0.028 / 0.028 | 0 / 0 / 0 | head.11.24->v.24.6 (-0.0008) |
| far | head.24.27 | q | head.17.24->q.24.27 | 0.0718 | 0.0038 | - | 4 / 0.108 / 0.108 | 0 / 0 / 0 | head.11.24->v.24.6 (-0.0008) |
| sdr | head.17.24 | q | head.14.4->q.17.24 | 0.2559 | 0.0130 | - | 12 / 0.979 / 1.003 | 1 / 0.011 / 0.011 | mlp.14.0->k.17.6 (0.0111) |
| sdr | head.17.25 | q | head.15.8->q.17.25 | 0.0510 | 0.0045 | - | 5 / 0.070 / 0.096 | 1 / 0.011 / 0.011 | mlp.14.0->k.17.6 (0.0111) |
| sdr | head.17.26 | q | head.15.8->q.17.26 | 0.0458 | 0.0019 | - | 5 / 0.134 / 0.134 | 1 / 0.011 / 0.011 | mlp.14.0->k.17.6 (0.0111) |
| sdr | head.17.27 | q | head.15.8->q.17.27 | 0.0607 | 0.0046 | - | 8 / 0.163 / 0.218 | 1 / 0.011 / 0.011 | mlp.14.0->k.17.6 (0.0111) |
| sdr | head.24.17 | q | head.17.24->q.24.17 | 0.0190 | 0.0051 | - | 1 / 0.019 / 0.019 | 0 / 0 / 0 | head.12.4->v.24.4 (0.0011) |
| sdr | head.24.20 | none | - | - | - | - | 0 / 0 / 0 | 0 / 0 / 0 | head.8.0->v.24.5 (0.0012) |
| sdr | head.24.26 | q | head.17.24->q.24.26 | 0.0253 | 0.0015 | - | 5 / 0.091 / 0.091 | 0 / 0 / 0 | mlp.14.0->k.24.6 (0.0020) |
| sdr | head.24.27 | q | head.17.24->q.24.27 | 0.0994 | 0.0081 | - | 5 / 0.172 / 0.172 | 0 / 0 / 0 | mlp.14.0->k.24.6 (0.0020) |
| ser | head.17.24 | q | head.15.8->q.17.24 | 0.2070 | 0.0091 | - | 11 / 0.637 / 0.706 | 0 / 0 / 0 | mlp.14.0->k.17.6 (0.0060) |
| ser | head.17.25 | q | head.15.8->q.17.25 | 0.0509 | 0.0035 | - | 3 / 0.078 / 0.078 | 0 / 0 / 0 | mlp.14.0->k.17.6 (0.0060) |
| ser | head.17.26 | q | head.15.8->q.17.26 | 0.0465 | 0.0035 | - | 7 / 0.122 / 0.122 | 0 / 0 / 0 | mlp.14.0->k.17.6 (0.0060) |
| ser | head.17.27 | q | head.15.8->q.17.27 | 0.0529 | 0.0036 | - | 7 / 0.007 / 0.160 | 0 / 0 / 0 | mlp.14.0->k.17.6 (0.0060) |
| ser | head.24.17 | none | - | - | - | - | 0 / 0 / 0 | 0 / 0 / 0 | mlp.13.0->k.24.4 (-0.0014) |
| ser | head.24.20 | q | head.17.24->q.24.20 | 0.0125 | 0.0028 | - | 1 / 0.012 / 0.012 | 0 / 0 / 0 | head.11.24->v.24.5 (-0.0012) |
| ser | head.24.26 | q | head.17.24->q.24.26 | 0.0241 | 0.0012 | - | 4 / 0.070 / 0.070 | 0 / 0 / 0 | mlp.14.0->k.24.6 (0.0017) |
| ser | head.24.27 | q | head.17.24->q.24.27 | 0.0712 | 0.0044 | - | 4 / 0.129 / 0.129 | 0 / 0 / 0 | mlp.14.0->k.24.6 (0.0017) |

L17H24-27 share KV group 6: their K/V cells are one test (spec 7); the strongest K/V cell is the same row for the four heads.

## Where the pressure enters (B4)

Neutral-twin paths into C_t's receivers at or above the floor; K/V paths placed by their split's top Segment, Q / MLP / Readout paths at the query positions (the Readout): that column is the receiver type, not a measured arrival position. A K/V split whose top Segment is `unsegmented` is post-clause by construction (pre-clause positions are identical in D and its twin) and has its own column; the pre-registered receiver category still calls it kv_unresolved (R25).

| task | paths >= floor | K/V clause (n / sum abs) | K/V post_clause | K/V post-clause unsegmented | K/V unresolved | K/V no split | Q / MLP / Readout receivers |
|---|---|---|---|---|---|---|---|
| far | 302 | 117 / 2.842 | 6 / 0.081 | 19 / 0.482 | 0 | 0 | 160 / 5.103 |
| sdr | 195 | 39 / 0.792 | 2 / 0.030 | 15 / 0.594 | 0 | 0 | 139 / 4.402 |
| ser | 361 | 147 / 3.601 | 17 / 0.310 | 20 / 0.629 | 0 | 0 | 177 / 5.099 |

far: strongest senders (summed |mean| over their paths >= floor):

| sender | paths | sum abs | signed | K/V clause abs | K/V post-clause abs (incl. unsegmented) | Q / MLP / Readout abs |
|---|---|---|---|---|---|---|
| mlp.6.0 | 20 | 0.877 | +0.733 | 0.359 | 0.000 | 0.518 |
| mlp.8.0 | 25 | 0.716 | +0.575 | 0.389 | 0.015 | 0.312 |
| mlp.7.0 | 24 | 0.707 | +0.596 | 0.336 | 0.000 | 0.371 |
| mlp.9.0 | 18 | 0.590 | +0.524 | 0.445 | 0.016 | 0.128 |
| mlp.4.0 | 14 | 0.397 | +0.325 | 0.123 | 0.000 | 0.274 |
| mlp.13.0 | 12 | 0.395 | +0.278 | 0.000 | 0.072 | 0.322 |
| head.13.23 | 6 | 0.329 | +0.237 | 0.000 | 0.023 | 0.306 |
| head.9.28 | 13 | 0.327 | -0.014 | 0.148 | 0.037 | 0.143 |
| head.14.4 | 8 | 0.326 | +0.326 | 0.000 | 0.037 | 0.290 |
| head.15.8 | 5 | 0.273 | +0.273 | 0.000 | 0.000 | 0.273 |
| mlp.11.0 | 9 | 0.251 | +0.227 | 0.142 | 0.043 | 0.065 |
| mlp.14.0 | 6 | 0.236 | +0.165 | 0.000 | 0.065 | 0.171 |

sdr: strongest senders (summed |mean| over their paths >= floor):

| sender | paths | sum abs | signed | K/V clause abs | K/V post-clause abs (incl. unsegmented) | Q / MLP / Readout abs |
|---|---|---|---|---|---|---|
| head.14.4 | 12 | 0.540 | +0.516 | 0.000 | 0.052 | 0.488 |
| mlp.13.0 | 14 | 0.509 | +0.275 | 0.000 | 0.171 | 0.338 |
| head.15.8 | 6 | 0.437 | +0.437 | 0.000 | 0.000 | 0.437 |
| head.14.5 | 7 | 0.382 | +0.382 | 0.000 | 0.088 | 0.294 |
| head.17.24 | 5 | 0.351 | +0.351 | 0.000 | 0.000 | 0.351 |
| mlp.6.0 | 10 | 0.311 | +0.194 | 0.121 | 0.000 | 0.191 |
| mlp.8.0 | 11 | 0.284 | +0.232 | 0.109 | 0.011 | 0.165 |
| head.15.11 | 8 | 0.265 | +0.240 | 0.000 | 0.000 | 0.265 |
| head.12.4 | 11 | 0.264 | +0.229 | 0.087 | 0.010 | 0.167 |
| mlp.12.0 | 10 | 0.251 | +0.184 | 0.095 | 0.029 | 0.127 |
| mlp.14.0 | 10 | 0.246 | +0.169 | 0.000 | 0.135 | 0.111 |
| mlp.7.0 | 7 | 0.221 | +0.193 | 0.055 | 0.000 | 0.166 |

ser: strongest senders (summed |mean| over their paths >= floor):

| sender | paths | sum abs | signed | K/V clause abs | K/V post-clause abs (incl. unsegmented) | Q / MLP / Readout abs |
|---|---|---|---|---|---|---|
| mlp.5.0 | 25 | 0.928 | +0.511 | 0.338 | 0.078 | 0.512 |
| mlp.6.0 | 31 | 0.817 | +0.496 | 0.559 | 0.035 | 0.223 |
| mlp.7.0 | 23 | 0.641 | +0.494 | 0.531 | 0.011 | 0.099 |
| mlp.11.0 | 19 | 0.441 | +0.348 | 0.258 | 0.037 | 0.146 |
| head.15.8 | 7 | 0.439 | +0.439 | 0.000 | 0.000 | 0.439 |
| mlp.13.0 | 12 | 0.393 | +0.209 | 0.035 | 0.117 | 0.241 |
| head.14.4 | 6 | 0.292 | +0.292 | 0.000 | 0.097 | 0.196 |
| head.14.5 | 6 | 0.279 | +0.279 | 0.000 | 0.125 | 0.154 |
| head.13.23 | 6 | 0.269 | +0.249 | 0.000 | 0.000 | 0.269 |
| head.17.24 | 5 | 0.269 | +0.269 | 0.000 | 0.000 | 0.269 |
| head.7.14 | 12 | 0.262 | +0.183 | 0.155 | 0.014 | 0.092 |
| head.12.6 | 9 | 0.244 | +0.211 | 0.167 | 0.011 | 0.067 |

## Completeness (neutral-twin sweep, direct paths into the Readout)

Each sender's mean is already a share of the clean-minus-twin gap, so the signed sums are shares of the gap. They are sums of single direct effects and can cancel (compare the absolute sum).

| task | C_t direct (share of twin gap) | outside C_t direct (share of twin gap) | outside abs | embed | unmeasured senders | flagged outside | top outside |
|---|---|---|---|---|---|---|---|
| far | +0.095 | +0.803 | 1.678 | 0.000 | 0 | 2 | mlp.31.0 +0.203, mlp.30.0 -0.111, head.31.0 +0.050, head.27.7 +0.040 |
| sdr | +0.191 | +0.811 | 1.794 | 0.000 | 0 | 4 | mlp.31.0 +0.205, mlp.30.0 -0.105, head.31.0 +0.063, head.22.28 +0.053 |
| ser | +0.200 | +0.774 | 1.763 | 0.000 | 0 | 4 | mlp.30.0 -0.127, mlp.31.0 +0.084, head.31.0 +0.061, head.27.7 +0.060 |

## Roles (cell d with the merged views; Components of C_t only)

| task | binder | selector | mover | suppressor | pressure reader | unknown | rows outside C_t (role) | missing views |
|---|---|---|---|---|---|---|---|---|
| far | 0 | 1 | 0 | 0 | 16 | 55 | mlp.31.0 (unknown), mlp.30.0 (unknown) | [] |
| sdr | 1 | 2 | 0 | 0 | 4 | 59 | mlp.31.0 (unknown), mlp.30.0 (unknown), head.31.0 (unknown), head.22.28 (unknown) | [] |
| ser | 1 | 1 | 0 | 0 | 5 | 71 | mlp.30.0 (unknown), mlp.31.0 (unknown), head.31.0 (unknown), head.27.7 (unknown) | [] |

## Cross-task roles (C3)

57 Components are in two or more C_t; 39 are in all 3, and 35 of those have the same role on every task. Components of every C_t with a role other than unknown on some task:

| Component | far part / role / category | sdr part / role / category | ser part / role / category |
|---|---|---|---|
| head.13.20 | core / pressure reader / kv_clause | core / pressure reader / kv_clause | core / unknown / kv_clause |
| head.13.21 | core / pressure reader / kv_clause | S_k / pressure reader / kv_clause | S_k / pressure reader / kv_clause |
| head.13.23 | S_k / pressure reader / kv_clause | S_k / pressure reader / kv_clause | S_k / pressure reader / kv_clause |
| head.14.4 | core / unknown / q | S_k / binder / q | core / unknown / q |
| head.17.24 | core / selector / q | S_k / selector / q | core / selector / q |
| head.17.26 | core / unknown / q | core / unknown / q | core / binder / q |
| head.24.27 | core / unknown / q | core / selector / q | core / unknown / q |

The full table (every Component of some C_t) is `docs/research/mechanism-analysis/phase3/roles_cross_task.csv`.

## Checks and cost

| task | twin sweep | same as grid | pre-clause top | twin n (gap-excl.) | twin Segment pass selected (K/V) | item-swap Segment selected (K/V) | rows outside C_t |
|---|---|---|---|---|---|---|---|
| far | neutral_twin | True | 0 | 100 (0) | 302 (0.056) | 13 (0.003) | 2 |
| sdr | neutral_twin | True | 0 | 100 (0) | 195 (0.029) | 12 (0.002) | 4 |
| ser | neutral_twin | True | 0 | 100 (0) | 361 (0.061) | 12 (0.002) | 4 |
