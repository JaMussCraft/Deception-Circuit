# B1 readings

Point estimates are ratios of means; brackets are 95% intervals from 2000 resamples clustered by pressure_id (seed 20261101).

## T1: loop closure

O, O_q and M_q are read on the rule estimator named in the estimator column (requested: offline; ruling R9 makes it offline). The controls (M_C3, C1, C2, M_S) are always offline. r_q is the dq_all arm's own margins and needs no estimator.

| task | n | estimator | O | O_q | M_q | r_q | M_C3 | max C1/C2 | M_S | verdict | label |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sdr_v2 | 100 | offline | 0.857 [0.823, 0.891] | 0.468 [0.434, 0.499] | 0.546 [0.511, 0.577] | 0.590 [0.556, 0.621] | -0.032 [-0.037, -0.027] | 0.022 | 0.821 [0.772, 0.867] | closes | closes, route-specific |

### T1 on the other estimator, reported beside the rule

Not the rule of record; the verdict column is what M_q on this estimator would give, for comparison only.

| task | estimator | O | O_q | M_q | verdict if read on it |
|---|---|---|---|---|---|
| sdr_v2 | forward | 0.871 [0.774, 0.965] | 0.479 [0.433, 0.525] | 0.550 [0.507, 0.596] | closes |

## T2: key-side or query-side

| task | n | P | r_Q | r_K | r_K - r_Q | r_out | verdict | frozen rule |
|---|---|---|---|---|---|---|---|---|
| sdr_v2 | 100 | 6.547 | 0.524 [0.488, 0.556] | -0.002 [-0.012, 0.008] | -0.526 [-0.556, -0.490] | 0.558 [0.524, 0.589] | query-side | query-side |
