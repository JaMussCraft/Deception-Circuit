# 02b — login dry-run tables (2026-10-25)

Ticket 02b, agent impl-02b. Phase-2 cells (spec section 4) on U and phase-3 path grids on the provisional C_t, every task, as `analyze_components.py --dry-run` resolved them on the Delta login node with the 02b code. Companion to `02b-handback.md`; scripts and logs in `02b-dryrun/`.

Login dry-runs of the phase-2 cells (spec section 4) on U and of the phase-3 path grids on the provisional C_t, all three tasks, run in-process on 2026-10-25 from the worktree with the 02b code (neutral-twin attention and path patching, `both` resolving to the twin on v2). The tables are also `reports/02b-dryrun-tables.md`; the driver, the grid script, the captured rows and the 21 logs are copied to `reports/02b-dryrun/` (the job tmp dir they ran from is deleted with the job).

### Phase-2 cells on U (123 heads, leaf; 1,000-row split; causal sample n = 100 in 13 batches of 8)

All 21 login dry-runs passed (`reports/02b-dryrun/logs/`, driver `reports/02b-dryrun/dryrun_driver.py`, grids `reports/02b-dryrun/grid_tables.py`). The forward counts are the CLI's own estimates; minutes are at 02a's measured H100 rate of 0.0389 s per forward unless the line says A40 (the attention estimate is the analysis's own eager-forward figure, A40-based).

| task | cell | segmentation | twin | attention_patterns | dla | knockout |
|---|---|---|---|---|---|---|
| far_v2 | P2 (U,D) attention+DLA+families | 1000 instance(s), 19 Segment | on 100 of 100 | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin 1000 instance(s) in 125 batch(es) read 2x, 4250 eager forward(s) ~13 min; total ~27 min A40 | pressure 1000 instance(s) in 125 batch(es); twin 1000 paired instance(s) of 1000 | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); all / item_swap |
| far_v2 | P2 (U,D) segment-resolved twin KO (clause) | 1000 instance(s), 19 Segment | on 100 of 100 |  |  | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); pressure_clause / neutral_twin |
| far_v2 | P2 (U,H) attention+DLA | 1000 instance(s), 19 Segment | n/a: the H split is the twin itself | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| far_v2 | P2 (U,F) attention+DLA | 1000 instance(s), 19 Segment | n/a: no Pressure Clause under nopressure | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| far_v2 | P2 (U,I) attention+DLA (twin) | 210 instance(s), 19 Segment | on 100 of 100 | pressure 210 instance(s) in 27 batch(es), 459 eager forward(s) ~87 s; twin 210 instance(s) in 27 batch(es) read 2x, 918 eager forward(s) ~3 min; total ~4 min A40 | pressure 210 instance(s) in 27 batch(es); twin 210 paired instance(s) of 210 |  |
| sdr_v2 | P2 (U,D) attention+DLA+families | 1000 instance(s), 19 Segment | on 100 of 100 | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin 1000 instance(s) in 125 batch(es) read 2x, 4250 eager forward(s) ~13 min; total ~27 min A40 | pressure 1000 instance(s) in 125 batch(es); twin 1000 paired instance(s) of 1000 | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); all / item_swap |
| sdr_v2 | P2 (U,D) segment-resolved twin KO (clause) | 1000 instance(s), 19 Segment | on 100 of 100 |  |  | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); pressure_clause / neutral_twin |
| sdr_v2 | P2 (U,H) attention+DLA | 1000 instance(s), 19 Segment | n/a: the H split is the twin itself | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| sdr_v2 | P2 (U,F) attention+DLA | 1000 instance(s), 19 Segment | n/a: no Pressure Clause under nopressure | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| sdr_v2 | P2 (U,I) attention+DLA (twin) | 788 instance(s), 19 Segment | on 100 of 100 | pressure 788 instance(s) in 99 batch(es), 1683 eager forward(s) ~5 min; twin 788 instance(s) in 99 batch(es) read 2x, 3366 eager forward(s) ~11 min; total ~16 min A40 | pressure 788 instance(s) in 99 batch(es); twin 788 paired instance(s) of 788 |  |
| ser_v2 | P2 (U,D) attention+DLA+families | 1000 instance(s), 19 Segment | on 100 of 100 | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin 1000 instance(s) in 125 batch(es) read 2x, 4250 eager forward(s) ~13 min; total ~27 min A40 | pressure 1000 instance(s) in 125 batch(es); twin 1000 paired instance(s) of 1000 | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); all / item_swap |
| ser_v2 | P2 (U,D) segment-resolved twin KO (clause) | 1000 instance(s), 19 Segment | on 100 of 100 |  |  | 5 named group(s) from docs/research/mechanism-analysis/jobs/02a-smoke-groups.json (sizes 1-4) = 91 more forward pass(es); pressure_clause / neutral_twin |
| ser_v2 | P2 (U,H) attention+DLA | 1000 instance(s), 19 Segment | n/a: the H split is the twin itself | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| ser_v2 | P2 (U,F) attention+DLA | 1000 instance(s), 19 Segment | n/a: no Pressure Clause under nopressure | pressure 1000 instance(s) in 125 batch(es), 2125 eager forward(s) ~7 min; twin n/a; total ~7 min A40 | pressure 1000 instance(s) in 125 batch(es); twin n/a |  |
| ser_v2 | P2 (U,I) attention+DLA (twin) | 249 instance(s), 19 Segment | on 100 of 100 | pressure 249 instance(s) in 32 batch(es), 544 eager forward(s) ~2 min; twin 249 instance(s) in 32 batch(es) read 2x, 1088 eager forward(s) ~3 min; total ~5 min A40 | pressure 249 instance(s) in 32 batch(es); twin 249 paired instance(s) of 249 |  |

Notes: (U,H) and (U,F) have no twin by construction (the H split *is* the twin; F has no clause), so their attention and DLA run the `pressure` and `honest_twin` conditions only. (U,I) runs on the inversion stand-in's filtered split (far 210, sdr 788, ser 249 rows) and pairs every row with its twin. The honest-instruction condition is `none` on every v2 cell (no Matched Honest pool, R1). The phase-2 knockout lines use the 02a placeholder family groups file (5 groups); the real family groups come from phase 2 itself.

### Phase-3 path grids on the provisional C_t = core | excl_t | ((D_t - H_t) - core)

`--path-counterfactual both` resolves to `item_swap` + `neutral_twin` on every v2 cell (the dry-run line prints `counterfactual(s): item_swap, neutral_twin`). The twin pairs 100 of 100 sampled instances on each task. The dry-run grid is heads-only (the expression's `- m` strips MLP leaves and no operand names single blocks); the MLP rows below are analytic through `path_patching.build_grid`/`cost` with the same batching.

| task | C_t variant | heads | MLPs | senders | receivers | cells | K/V cells | forwards per counterfactual | H100 min per cf | both cfs | position pass, every cell selected (worst) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| far_v2 | heads only (dry-run) | 47 | 0 | 48 | 110 | 2367 | 1292 | 31,421 | 20.4 | 40.7 | 380,692 fwd = 247 min |
| far_v2 | + 10 placeholder MLPs | 47 | 10 | 58 | 120 | 3224 | 1614 | 42,692 | 27.7 | 55.4 | 482,508 fwd = 313 min |
| far_v2 | + S_k heads (single_k20) + 10 MLPs = ticket 03's C_t | 58 | 10 | 69 | 145 | 4559 | 2312 | 60,190 | 39.0 | 78.0 | 689,624 fwd = 447 min |
| sdr_v2 | heads only (dry-run) | 48 | 0 | 49 | 105 | 2291 | 1168 | 30,446 | 19.7 | 39.5 | 348,088 fwd = 226 min |
| sdr_v2 | + 10 placeholder MLPs | 48 | 10 | 59 | 115 | 3068 | 1400 | 40,677 | 26.4 | 52.7 | 425,594 fwd = 276 min |
| sdr_v2 | + S_k heads (single_k20) + 10 MLPs = ticket 03's C_t | 56 | 10 | 67 | 133 | 4067 | 1910 | 53,768 | 34.9 | 69.7 | 577,538 fwd = 374 min |
| ser_v2 | heads only (dry-run) | 51 | 0 | 52 | 116 | 2793 | 1516 | 37,011 | 24.0 | 48.0 | 447,096 fwd = 290 min |
| ser_v2 | + 10 placeholder MLPs | 51 | 10 | 62 | 126 | 3728 | 1876 | 49,296 | 32.0 | 63.9 | 560,326 fwd = 363 min |
| ser_v2 | + S_k heads (single_k20) + 10 MLPs = ticket 03's C_t | 63 | 10 | 74 | 150 | 5302 | 2684 | 69,914 | 45.3 | 90.7 | 800,826 fwd = 519 min |

- far_v2: placeholder MLP blocks (single_k20 rule, S2p rank, layer 0 never) = layers [4, 6, 7, 8, 9, 11, 13, 14, 15, 16]; S_k adds 11 head(s) beyond the named union.
- sdr_v2: placeholder MLP blocks (single_k20 rule, S2p rank, layer 0 never) = layers [4, 6, 7, 8, 12, 13, 14, 15, 16, 19]; S_k adds 8 head(s) beyond the named union.
- ser_v2: placeholder MLP blocks (single_k20 rule, S2p rank, layer 0 never) = layers [1, 5, 6, 7, 11, 13, 14, 15, 16, 19]; S_k adds 12 head(s) beyond the named union.

Position-specific pass (the receiver category's input): per selected K or V cell 273 forwards (19 Segments + union check, 13 batches), per selected Q/MLP/Readout cell 26 forwards, plus 26 to re-capture the streams. The worst case above assumes every cell is selected. Under R25 decision A the two counterfactuals run at different thresholds: the item-swap pass keeps `--path-position-threshold 0.05` and the neutral-twin pass runs at `--path-twin-position-threshold 0.01` (the receiver category's floor; the flag added in the review fixes so that the item swap is not dragged down with it). The threshold changes nothing but the selected fraction f of the K/V cells, so the cost is tabulated per selected share, at ticket 03's full C_t (third row of each task) and 0.0389 s per forward:

| task | K/V cells at C_t | forwards per 1 % of K/V cells selected | item_swap at 0.05, f = 3 % (v1 grids selected a few percent) | neutral_twin at 0.01, f = 10 % | neutral_twin at 0.01, f = 25 % | neutral_twin at 0.01, f = 100 % (worst) |
|---|---|---|---|---|---|---|
| far_v2 | 2312 | 6,312 fwd = 4.1 min | 12.3 min | 40.9 min | 102 min | 409 min |
| sdr_v2 | 1910 | 5,214 fwd = 3.4 min | 10.1 min | 33.8 min | 85 min | 338 min |
| ser_v2 | 2684 | 7,327 fwd = 4.8 min | 14.3 min | 47.5 min | 119 min | 475 min |

(The Q/MLP/Readout cells add 26 forwards each and the stream re-capture 26 per pass; both are small beside the K/V term and are left out of the per-share column.) Which share clears 0.01 is not knowable before the agnostic pass: the smoke's selected fraction at 0.01 on its 307-cell grid, and its measured path and Segment forward rates on the H100, are the planning numbers ticket 05 reads off this table. If the fraction lands near 25 % the twin's Segment pass alone is 1.4 to 2 H100 h per task, which is the number decision A's "provided the cost fits ticket 05" turns on.

Completeness sweep (dry-run line, item_swap only): 1,057 senders into the Readout, 13,767 forwards per task = 8.9 H100 min.

Per task at ticket 03's full C_t (third row), both counterfactuals plus the sweep and a 10 percent position pass: far_v2 ~132 min; sdr_v2 ~116 min; ser_v2 ~152 min on an H100 before the 8 min model load, if a path forward costs what a knockout forward does. The path forwards capture every sender and run a patched receiver, so the smoke's measured path rate replaces 0.0389 here (it is what the smoke is for).
