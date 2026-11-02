# B1 readings

Point estimates are ratios of means; brackets are 95% intervals from 2000 resamples clustered by pressure_id (seed 20261101).

## T1: loop closure

O, O_q and M_q are read on the rule estimator named in the estimator column (requested: offline; ruling R9 makes it offline). The controls (M_C3, C1, C2, M_S) are always offline. r_q is the dq_all arm's own margins and needs no estimator.

| task | n | estimator | O | O_q | M_q | r_q | M_C3 | max C1/C2 | M_S | verdict | label |
|---|---|---|---|---|---|---|---|---|---|---|---|
| far_v2 | 100 | offline | 0.781 [0.762, 0.802] | 0.281 [0.261, 0.307] | 0.360 [0.337, 0.395] | 0.342 [0.323, 0.366] | -0.031 [-0.036, -0.026] | 0.175 | 0.998 [0.979, 1.016] | bypass | bypass |
| ser_v2 | 100 | offline | 0.752 [0.704, 0.783] | 0.347 [0.318, 0.363] | 0.462 [0.437, 0.485] | 0.451 [0.426, 0.473] | -0.035 [-0.040, -0.031] | 0.111 | 1.038 [0.984, 1.093] | bypass | bypass |

### T1 on the other estimator, reported beside the rule

Not the rule of record; the verdict column is what M_q on this estimator would give, for comparison only.

| task | estimator | O | O_q | M_q | verdict if read on it |
|---|---|---|---|---|---|
| far_v2 | forward | 0.771 [0.706, 0.847] | 0.275 [0.245, 0.312] | 0.356 [0.335, 0.390] | bypass |
| ser_v2 | forward | 0.781 [0.738, 0.844] | 0.349 [0.328, 0.371] | 0.447 [0.413, 0.474] | bypass |

## T2: key-side or query-side

| task | n | P | r_Q | r_K | r_K - r_Q | r_out | verdict | frozen rule |
|---|---|---|---|---|---|---|---|---|
| far_v2 | 100 | 9.886 | 0.321 [0.302, 0.344] | -0.012 [-0.017, -0.007] | -0.333 [-0.359, -0.312] | 0.327 [0.310, 0.349] | query-side | query-side |
| ser_v2 | 100 | 5.960 | 0.426 [0.396, 0.446] | 0.014 [0.006, 0.018] | -0.412 [-0.432, -0.384] | 0.433 [0.407, 0.454] | query-side | query-side |
