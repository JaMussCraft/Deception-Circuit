# 02a login dry-runs (2026-10-25, Delta login node, mgnp env, CPU only)

All 48 dry runs exited 0: phase 1B (9 cells x 3 tasks) and the 1C invocations (7 x 3; I on a fixture). Driver
`/u/swong2/.claude/jobs/1c836bb8/tmp/impl02a/dryrun_driver.py`, one stdout log per run with its full argv in
`/u/swong2/.claude/jobs/1c836bb8/tmp/impl02a/dry/logs/`, rows in `.../dry/dryrun_rows.json`.

## Binding (every cell)

U = `(Df|Hf|Ds|Hs|De|He)-m` at leaf, m = `outputs/_launch_mechanism_v2/evals/operands/allmlp_nomb_v2`: 123 heads, 0 MLP
blocks, 17 layers. The six atomic runs bound as references (`far_D` ... `ser_H`): 58 / 60 / 60 / 58 / 55 / 69 heads
of U, matching HB (g). Test set by `--task-from`: D and H their own runs, F the tracked nopressure stand-ins, I a
config-only stand-in with `deception_condition: inversion` (fixture under the tmp dir until ticket 08 lands).

## Per cell (the same on all three tasks unless stated)

| cell | test set | segmentation | sample | pairing | knockout / DLA estimate |
| --- | --- | --- | --- | --- | --- |
| 1B S1 | D | 1000 rows, 19 Segments (v2 scheme) | 100, seed 0, 8 strata | twin 100 of 100 | sweep 1056 x 13 batches = 13,754 forwards, about 11.4 min H100 (extrapolated) |
| 1B S2 | D | same | same | twin 100/100 | 13,754, neutral_twin, all positions |
| 1B S2p | D | same | same | twin 100/100 | 13,754, neutral_twin, `after=pressure_clause,exclude=readout`, mlp.0.0 excluded from ranking |
| 1B S3 | D | same | same | twin 100/100 | 13,754, neutral_twin, readout |
| 1B S4 | D | same | same | twin 100/100 | 13,754 + 250 bank forwards = 14,004, about 11.6 min |
| 1B S5 | H | same | 100, seed 0 (the same ids as D) | not applicable (H is the twin) | 13,754, item-swap |
| 1B S6 | F | same (no `pressure_clause`) | 100, seed 0 (the same ids as D) | not applicable (no clause) | 13,754, item-swap |
| 1B L (D) | D | same | - | twin 1000 of 1000 | DLA: pressure 1000 rows (125 batches) + neutral_twin 1000 paired (2 forwards each) |
| 1B L (F) | F | same | - | - | DLA: pressure 1000 rows |
| 1C S7 | I fixture (600 rows) | 600 rows | 100, seed 0 | twin 100/100 | 13,754, neutral_twin, post-clause, mlp.0.0 excluded |
| 1C greedy | D | 1000 | 100, seed 0 | twin 100/100 | pool 50, k 20: 810 group knockouts = 11,050 forwards, about 9.1 min |
| 1C held-out D | D | 1000 | 100, seed 1, the S1 sample excluded (100 ids; disjoint, checked) | twin 100/100 | 300 groups (2 selectors x k grid + 20 nulls each, routing x3, named x3; sizes 1-996) = 3,926 forwards, about 3.3 min |
| 1C held-out H (ii) | H | 1000 | seed 1, same exclusion (same ids as held-out D, checked) | n/a | 17 groups, item-swap = 247 forwards |
| 1C held-out F (ii) | F | 1000 | seed 1, same exclusion | n/a | 17 groups = 247 forwards |
| 1C R-inv D | D | 1000 | `--include-ids` = held-out D ids that survive I: 60 / 59 / 57 (far / sdr / ser, fixture) | twin on all | 1 group = 24 forwards |
| 1C R-inv I | I fixture | 600 | the same included ids | twin on all | 1 group = 24 forwards |

Checked from the written `sample.json`s (derived): on every task the S5 (H) and S6 (F) samples are the same 100 ids
as S1 (D); the held-out D sample is disjoint from S1; the held-out H sample equals the held-out D sample.

Per-task phase-1B forwards (7 sweeps + the bank): 96,528 forwards, about 80 min on an H100 at the extrapolated
0.0497 s per forward, plus L. Spec §4 costed 7 x 13 min = 91 min; the smoke job replaces the rate with a measurement.

## Smoke and drift job file (`docs/research/mechanism-analysis/jobs/02a-smoke-drift.batch`), Delta login check

`analyze_components.py batch <file> --dry-run` with the suites redirected to tmp and the untracked v1 runs read from
the main checkout: 8 of 8 lines ok. Forwards: drift 13,754; S2p at n = 8: 1,058; mean 125 + 250 bank; zero, readout,
clause 125 each; groups and greedy (n = 100, seed 1) 91 + 1,989; DLA 1,000 rows (pressure + twin pair).
