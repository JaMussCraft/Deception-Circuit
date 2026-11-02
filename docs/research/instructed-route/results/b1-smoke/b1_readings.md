# B1 readings

Point estimates are ratios of means; brackets are 95% intervals from 2000 resamples clustered by pressure_id (seed 20261101).

## T1: loop closure

| task | n | O | O_q | M_q | r_q | M_C3 | max C1/C2 | M_S | verdict | label |
|---|---|---|---|---|---|---|---|---|---|---|
| far_v2 | 8 | 0.732 [0.561, 0.896] | 0.275 [0.194, 0.375] | 0.376 [0.279, 0.464] | 0.335 [0.274, 0.419] | -0.024 [-0.035, -0.013] | 0.196 | 0.992 [0.965, 1.020] | bypass | bypass |
| ser_v2 | 8 | 1.033 [0.830, 1.206] | 0.428 [0.273, 0.503] | 0.414 [0.311, 0.485] | 0.464 [0.406, 0.489] | -0.044 [-0.061, -0.024] | 0.083 | 0.990 [0.914, 1.192] | bypass | bypass |

## T2: key-side or query-side

| task | n | P | r_Q | r_K | r_K - r_Q | r_out | verdict | frozen rule |
|---|---|---|---|---|---|---|---|---|
| far_v2 | 8 | 11.054 | 0.310 [0.253, 0.397] | -0.012 [-0.034, 0.004] | -0.322 [-0.402, -0.260] | 0.325 [0.268, 0.404] | query-side | query-side |
| ser_v2 | 8 | 5.204 | 0.418 [0.324, 0.452] | 0.013 [-0.001, 0.024] | -0.405 [-0.438, -0.316] | 0.445 [0.383, 0.468] | query-side | query-side |
