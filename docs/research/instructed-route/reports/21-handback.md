# Hand-back 21: B1 tickets 5 and 6, the T1 sweeps, controls, path patching and the readings script

Agent: ticket implementer (Claude Opus 5.5), session claude-230e4716. Ticket: `docs/research/instructed-route/plans/B1-plan.md` section 5, tickets 5 and 6 (sections 1.2, 1.3, 1.5, 2.3 and ruling R1 in `spec.md`). Status: resolved, except the full-suite regression comparison, which the orchestrator runs.

## What changed

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/component_analysis/route_closure.py`, ticket 5. It adds both T1 estimators, the joint swap, controls C1 to C3, the S_k reference, the position-resolved path patching of plan 1.5 and 2.3, three flags, the `g3` gate, `t1.sweeps`, `t1.summary` and `t1.path_patching`. The schema is in the module docstring.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_route_closure_t1.py`, new (22 tests: 8 pure, 14 on the tiny GQA Llama under nnsight 0.7.0).
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/route_closure_readings.py`, ticket 6, new.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_route_closure_readings.py`, new (18 tests, synthetic JSON, no torch).
- Committed by the orchestrator from the worktree, **outside this ticket's ownership**: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_route_closure_t2.py`, one line. It asserted that `t1.sweeps.status` starts with "not implemented"; it now asserts "computed". The lead was told by message. Decline it by file list if preferred, but the ticket-4 run test then fails.
- Committed by the orchestrator from the worktree: this file.

`component_analysis/path_patching.py` was not edited. The module calls `receiver_inputs(..., sender_positions=mask)` and `readout_from_receivers` directly, so no mask pass-through was needed.

Flags added: `--route-path-patching {on,off}` (default on), `--route-pp-feeders KEYS` (default `head.14.4,head.15.8,mlp.13.0,mlp.14.0,mlp.15.0`) and `--route-c2-layers LOW-HIGH` (default `8-16`). `--route-sweep`, `--route-deciding-set` and `--route-pp-top` are now used.

How the ticket-5 pieces work:

- **Outside senders.** These are every head and MLP block outside C_t and outside the quartet. The embedding is never one (`outside_senders`).
- **Normalisation.** Each sender's effect is its mean drop over the mean twin gap G. `sweep_streams` builds `path_patching.Streams` with `gap = G`, and its clean outputs are the senders only. `summarize_sweep` divides the mean drop by the mean G. The arm's own gap is never used.
- **Estimator (a).** `forward_sweep` runs one `sweep_readout` forward per sender, on the twin and on `dq_all`. It is the rule of record for O and O_q.
- **Estimator (b).** `offline_direct_effects` replaces one sender's contribution in D's captured final residual by its X contribution. It reads the result through the real final norm in fp32, using only the two unembedding rows, chunked. It runs on the twin, the three dq arms and every control.
- **Joint swap.** `forward_joint` and `offline_direct_effects(joint=...)` swap every summed sender at once.
- **Controls.** `build_t1_arms` builds the T1 controls. C1 reuses the T2 layer-17 head draws. C2 draws heads with `draw_c2_heads`, seeded with "c2_heads". C3 is `c3_push`, built by `solve_push` (closed form at D's fixed layer-L scale) and `direction_push_bank`. S_k restores the deciding set post-clause.
- **Excluded sites.** Each arm's own written sites are left out of its O: the drawn heads, the deciding set, and `mlp.L` for the push.
- **Path patching.** It makes a second pass over the batches, after the top writers are ranked by |e_s(T)| on the whole sample. The quartet is written at `readout`, `post_clause_no_readout` and their union `post_clause`. Plan 2.3 writes each feeder and each layer below L as one group into the quartet's q at the Readout and into k at the options.

The script `scripts/route_closure_readings.py` reads one `route_closure.json` per task and writes `b1_readings.json` and `b1_readings.md` to `--out-dir` (default `docs/research/instructed-route/results`). It reports:

- M_q, the controls' M values, r_Q, r_K and r_out.
- The T2 reading and the frozen-rule verdict beside it.
- The T1 verdict and the R1 label with every qualifier that applies.
- Per-instance medians.
- A 95% interval from 2,000 resamples clustered by `pressure_id` with seed 20261101. Whole clusters are drawn with `numpy.random.default_rng`, and an instance with no pressure_id is its own cluster.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_route_closure*.py tests/test_path_patching*.py tests/test_analyze_components_registry.py
```

Observed: 180 passed in 64.45s.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_route_closure_t1.py tests/test_route_closure_t2.py tests/test_route_closure_readings.py tests/test_path_patching.py tests/test_path_patching_cli.py tests/test_path_patching_neutral_twin.py tests/test_path_patching_passes.py tests/test_path_patching_sender_positions.py tests/test_analyze_components_registry.py
```

Observed: 106 passed, 31 skipped (the nnsight 0.7.0 model tests), 3 warnings, 0 failed.

The counts per file come from separate runs of each file. The t1 row adds the offline-only run test, which was written after those runs and is counted in the two totals above.

| file | mgnp | base 3.9 |
|---|---|---|
| `tests/test_route_closure_t1.py` | 22 passed | 8 passed, 14 skipped |
| `tests/test_route_closure_readings.py` | 18 passed | 18 passed |
| `tests/test_route_closure_t2.py` | 23 passed | 12 passed, 11 skipped |

What the ticket-5 tests assert on the tiny model:

- **Normalised by G.** The forward sweep divides by G and not by the arm's gap. The case is built so the two differ by about a third. The effect equals `normalized_effect` on the G-gap streams, and O is not the arm-gap ratio.
- **Estimators agree.** Offline and forward drops agree within 1e-3 for every outside sender, and on the joint swap, for both the twin and D_q.
- **Joint swap.** The joint swap equals a direct forward with every outside sender taken from X and every other sender frozen at D. This holds within 1e-6 for the forward estimator and 1e-3 for the offline one. On the twin it is not the sum of the single swaps.
- **Exclusions.** O excludes C_t, the quartet and the embedding, and the outside count is checked. Each arm leaves its own written sites out of its O: S_k's keys, C3's `mlp.1`, and the drawn heads.
- **C3.** The push moves the fixed-scale lens exactly as D_q does, within 1e-4. The direction is a unit vector, and the push writes only at the Readout.
- **Masks.** The sender masks and the receiver masks start and end where plan 1.5 says. A pre-Readout-only quartet write gives zero at the Readout's MLP input. A Readout-only write equals a hand-built two-pass patch.
- **run().** It writes the sweeps, the controls, `g3` (passed, differences below 1e-3), the summary, and path patching with the skipped feeder `head.14.4`. A forward-only run says the controls need the offline estimator. An offline-only run reads the rule on the offline estimator, leaves G3 undecided and ranks the path-patching writers by the offline |e_s(T)|. A T2-only run says T1 is not selected.
- **Estimate.** It counts the sweep forwards and the path-patching forwards.
- **Readings compatibility.** The readings script reads the JSON that `run()` writes and reproduces M_q, O, r_q, M_C3 and the C1 set.

The ticket-6 tests check:

- the restore and reverse share formulas, and M_q, O, O_q, r_q, r_Q, r_K and r_out as ratios of means, with their per-instance medians;
- the T1 verdict at 0.4999 (bypass) and 0.5000 (closes);
- the T2 verdict at 0.1499 and 0.1500 in both directions, and the ceiling at 0.1499 and 0.15;
- the R1 labels: route-specific, generic amplification, not specific, both qualifiers at once, bypass, and controls not computed;
- that the bootstrap draws whole clusters, is seeded, and matches `default_rng` draw by draw;
- that the interval is reproducible and brackets the point;
- that `main` writes both files, and refuses a skipped cell by path.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **Nothing ran on the 8B model.** G3 on bf16, the C3 miss on bf16, and the memory and wall time of the capture-all arms, the forward sweep and the second path-patching pass are not measured. The `--dry-run` estimate counts forwards, but it prices them at the A40 per-forward rate. The B1 smoke's `--timings` replace it.
- **The full suite was not run, by instruction.** The orchestrator runs it and compares failures by name.
- **No batch files or dry runs.** Those are ticket 7.

## Open questions

1. **The one-line edit to the ticket-4 test.** It is outside my ownership but required. Default: commit it with ticket 5.
2. **Each arm's own written sites are left out of its O.** These are C1's and C2's drawn heads, the deciding set for S_k, and `mlp.L` for C3. This matches the quartet, which sits in C_t and so is left out of O_q. Default: keep. The per-sender values of the excluded sites stay in the JSON, marked as not summed.
3. **C3's bf16 rounding.** The fixed scale is D's layer-L residual at the Readout. On bf16 the pushed MLP output is rounded, so the achieved lens change can miss the target. The JSON records the target, the achieved change and `max_abs_miss`; there is no correction step. Default: read `max_abs_miss` in the smoke, and add one correction forward only if it exceeds about 0.01 logits.
4. **Path-patching receivers.** The `mlp_in` receivers are written at the Readout only, which the plan leaves open. The k and v receivers are written post-clause with the Readout included, and a group's k or v write also reaches its other heads. The top 20 writers by |e_s(T)| are taken over every outside sender, so writers the quartet cannot reach are listed as unreachable and get no forward. Default: keep. The alternative is to rank among reachable writers only.
5. **Plan 1.5's third sender mask.** I added `post_clause`, the union of the two masks. It equals every position, so it is comparable with O_q. Default: keep.
6. **The T2 ceiling and the frozen rule.** The reading is "indeterminate, ceiling below 0.15" whenever r_out is below 0.15, as the brief and plan 2.2 say. The frozen spec rule does not mention the ceiling, so `frozen_rule_verdict` is reported beside it. Default: report both, and the orchestrator names the verdict of record if they ever differ.
7. **Which estimator each T1 reading uses.** The closes-or-bypass verdict uses the rule-of-record M_q, the forward one. R1's comparisons use the offline M_q against the offline controls, because plan 1.2 says arms are compared on one estimator. Default: keep.
8. **When two R1 qualifiers hold.** If generic amplification and not specific both hold, the label is the first in R1's order, generic amplification, and `qualifiers` lists both. Default: keep.
9. **Medians with small denominators.** Per-instance medians leave out instances whose denominator has an absolute value below 1e-3 logits, and count them. Default: keep.
10. **The schema string.** It stays `route_closure/1`, because no file has been written yet and the change only adds fields. Default: keep.
