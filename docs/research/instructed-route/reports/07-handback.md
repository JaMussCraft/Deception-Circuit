# Hand-back 07: B1 ticket 4, the route_closure core and the T2 arms

Agent: ticket implementer (Claude Opus 5.5), session claude-230e4716. Ticket: `docs/research/instructed-route/plans/B1-plan.md` section 5, ticket 4 (sections 0, 1.1, 2 and the section 3 interface). Status: resolved, except the full-suite regression comparison (see Open questions); the T1 sweeps are ticket 5.

## What changed

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/component_analysis/route_closure.py`, new analysis module (core, T2 arms and controls, T1 D_q arms, flags, estimate, JSON writer; the JSON schema is in its docstring).
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/component_analysis/registry.py`, one line added to `ANALYSES` (with its blank-line separator).
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_route_closure_t2.py`, new test file (23 tests; 12 pure, 11 on the tiny GQA Llama under nnsight 0.7.0).
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/07-handback.md`, this file.

No other file was edited. `analyze_components.py`, `path_patching.py` and `knockout.py` were only read. The module calls `path_patching.counterfactual_pair`, `NEUTRAL_TWIN`, `heads_per_group` and `seconds_per_forward`, which predate tickets 2 and 3.

Interface, as built:

- `capture_pair(model, batch, segmentations, *, keys=None) -> PairStreams | None` runs D and T whole and captures every sender and receiver key. It holds `d` and `t` (each a `Stream` with outputs and the fp32 margin), `gap` (G = m(D) − m(T)), `ids`, `rows`, `pressure_ids`, `readout`, `target`, `distractor`, `segmentations` and `masks`. It refuses a twin that differs in length, or that differs outside the Pressure Clause.
- `restore_bank(source, keys, mask) -> {key: hooks.Replacement}`.
- `run_arm(model, pair, bank, capture_keys=(), *, base="D") -> ArmResult(margins, outputs)`. The `base` keyword was added for the reverse direction.
- `position_masks`, `draw_control_heads`, `draw_control_positions`, `build_arms`, `load_ct` and `load_deciding_set` are the pure helpers.
- Flags: `--route-tests`, `--route-direction`, `--route-sweep`, `--route-control-draws`, `--route-control-seed`, `--route-ct`, `--route-deciding-set FILE:NAME`, `--route-pp-top`, and two additions, `--route-quartet LAYER:H,...` (default `17:24,25,26,27`, so the tiny model can be tested) and `--route-max-batches` (smoke runs).
- Output: `<cell>/route_closure/route_closure.json`, schema `route_closure/1`. It carries per-instance `m_D`, `m_T`, `G` and `pressure_id`; every arm's per-instance margins and mean; the gate results; the control draws; and the first batch's masks as Segment names plus token indices. No head-table columns are written.

`k` and `q` are written at the `k_proj` and `q_proj` outputs, which is before RoPE. `hooks._traced_forward` confirms this.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_route_closure_t2.py tests/test_analyze_components_registry.py
```

Observed: 36 passed, 0 failed.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_route_closure_t2.py tests/test_analyze_components_registry.py
```

Observed: 25 passed, 11 skipped (the tiny-model tests, which need nnsight 0.7.0), 0 failed.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_route_closure_t2.py tests/test_analyze_components_registry.py tests/test_analyze_components_end_to_end.py tests/test_analyze_components_segmentation.py
```

Observed: 55 passed, 0 failed (final code).

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_route_closure_t2.py tests/test_analyze_components_registry.py tests/test_analyze_components_end_to_end.py tests/test_analyze_components_segmentation.py
```

Observed: 44 passed, 11 skipped, 0 failed (final code).

The tests cover the following:

- **Gate G1.** An empty bank gives m(D) under `torch.equal`.
- **Gate G2.** Restoring every `hooks.all_component_keys` key, embedding included, gives m(T) within 1e-5. A one-off script found it bit-exact on the tiny model, with max abs diff 0.0. The reverse direction is also checked.
- **K-group isolation.** A `k.1.1` write, at every position and at the options, changes only that group's two heads. With the option mask, it changes nothing before the first option.
- **Pre-clause exact zero.** Writing K and V at the pre-clause mentions gives m(D) bit-identically.
- **Masks.** The option mask is exactly the four option Segments and is disjoint from the pre-clause mentions. An absent option Segment is refused by name.
- **Control draws.** Head draws are seeded, reproducible, and disjoint from the quartet and C_t. Position draws are reproducible per instance id across batch orders, and they avoid the options, the Readout and the clause.
- **Registry and help.** The registry lists `route_closure`, and `analyze_components.build_parser().format_help()` shows every flag.
- **run() wiring.** On a stub context, `run()` writes the schema. A no-twin cell and a v1 cell write the skipped file. The estimate counts forwards and says "not applicable" without a twin.

CPU check on the real held-out samples, with the Llama tokenizer and no model. The script `/u/swong2/.claude/jobs/230e4716/tmp/realmasks.py` was run with mgnp from the worktree. It sits in the job's temporary directory, which is deleted with the job, so the two lines below are the record. The script loads each task's test split and its `{far,ser}_heldout_D_sample.json` ids through `dataloaders.causal_batches`. For every row it runs `_check_alignment`, `position_masks` and `draw_control_positions` (5 draws, 4 tokens).

```
far instances 100 with twin 100 option-token counts [4] eligible random tokens min/max 39 39 scheme mechanism_v2 pressure_ids 11 None in pids False
ser instances 100 with twin 100 option-token counts [4] eligible random tokens min/max 42 42 scheme mechanism_v2 pressure_ids 14 None in pids False
```

All 200 twins pass the alignment check. The far options are `' vision', ' hearing', ' vision', ' hearing'` and the Readout token is `' is'`.

Full suites (`tests/`, both interpreters) were started in the background and stopped unfinished at the lead's direction. When stopped, mgnp was at about 2% and base 3.9 at about 28%, with some failures already shown as `F` in the progress dots. Their test names were not captured, so no regression comparison by name was done. The command is under Open questions.

## Execution evidence

Not applicable: no runs.

## What is NOT done

These are ticket 5's parts. The JSON lists them under `not_implemented` and writes `t1.sweeps.status = "not implemented: ticket 5"`.

- `offline_direct_effects`: the fp32 decomposition through the real norm, normalized by `pair.gap`.
- `forward_sweep`: `path_patching.Streams` with the gap overridden to G, the rule-of-record estimator for O and O_q.
- The joint swap of all outside senders.
- Controls C1 and C2 read with the offline estimator, and C3 (`direction_push_bank`).
- The S_k reference: the deciding set restored post-clause. `--route-deciding-set` is parsed, loaded and recorded, but not used yet.
- The position-resolved path patching of plan sections 1.5 and 2.3. `--route-pp-top` is parsed and recorded only.

The memory cost of `capture_pair` on 8B is not measured. It captures every sender and receiver for both streams, about 2.3 GB per stream at batch 8 and 250 tokens in bf16 by arithmetic. The smoke job's `--timings` replace this estimate.

## Open questions

- **Full-suite regression comparison is not done.** Run these from the worktree in the background; each takes more than 10 minutes. Compare the failing names against the 8-name worktree baseline in shared memory `deception-circuit-worktree-testing.md` (the MASK repo-root test, `test_deception_common` word-reuse ×3 and length-matching, `test_three_specs_registered`, `test_pressure_pools_are_well_formed[ser]`, and `test_hyperparameters_are_identical_across_the_three_mechanisms`). A failure in the path_patching, knockout or analyze_components tests may come from tickets 1 to 3's concurrent edits. Default: the orchestrator runs it before committing.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider -rf tests 2>&1 | grep -E "^FAILED|^ERROR|passed|failed"
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider -rf tests 2>&1 | grep -E "^FAILED|^ERROR|passed|failed"
```

- **Readout in the post-clause K and Q arms.** `k_post_clause` and `q_post_clause` include the Readout, as the ceiling of the option restriction. Default: keep it. `dq_post_clause_no_readout` is the only arm that excludes it.
- **The pre-clause exact-zero check writes both K and V** of the quartet group at `item_1_intro`, `item_2_intro` and `designation_site` (`kv_preclause_mentions`). Default: keep one combined arm.
- **Control heads without `--route-ct`.** They are drawn outside the cell's own circuit, which equals C_t when the batch line uses the 05-p3 `--expr Ct=...` composition. The JSON records `grid.source` and `grid.matches_cell`. Default: ticket 7's batch lines pass `--route-ct docs/research/mechanism-analysis/phase3/ct.json` explicitly.
- **Default-run reach.** Registering the module means every `analyze_components.py` run without `--analyses` reaches it. A v1 or no-twin cell then writes a skipped file and spends no forwards. Default: accept, since batch lines name `--analyses`.
- **Head-table columns.** None are written; the coverage of the twin ids is still declared. Default: JSON only.
