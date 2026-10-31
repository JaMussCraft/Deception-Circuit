# 15 — Knockout completeness sweep over every Component of the model

**What to build:** The interchange knockout runs over every head and MLP block of the model, not only the circuit's Components, on the same 100 instances as the single-Component knockouts, and writes a ranked list with circuit membership marked, beside the existing results.

**Blocked by:** 13 — Paired column names, per-column coverage meta, multi-job cells, lifted job budget.

**Status:** resolved

- [x] `--knockout-completeness-sweep` knocks out each of the model's heads and MLP blocks one at a time with the interchange ablation ticket 07 uses, on the grid's sample (same instance ids as `knockout.json`), through ticket 07's `knock_out_groups` loop; `knockout/sweep.json` with a ranked list, circuit membership, drop, standard error and accuracy per Component, plus a PNG twin with circuit Components highlighted.
- [x] Head-table columns for circuit Components (`knockout.sweep_rank` and a flag) and a per-column coverage declaration; non-circuit Components clearing a `--knockout-sweep-threshold` (default stated and justified) are listed in the JSON, not added as head-table rows.
- [x] `--dry-run` sizes the sweep (about 1057 Components times the batch count, one forward each) and the estimate is calibrated against the job.
- [x] Tests: on the tiny model the sweep's entry for a circuit Component equals its single knockout exactly; the sweep covers every Component the model's geometry declares.
- [x] Verified by a Slurm run on SDR nls0.3 at head-granularity delta (multi-hour is fine; rehearse with `--dry-run`, `--time` on the command line); the ticket records the top non-circuit Components and whether they match the path-patching sweep's seven.
- [x] Subagent code review against the spec completed and findings addressed.

## Comments

### What was built

Two commits on `ca/15-knockout-completeness-sweep`, base `4ba2877`:

    bd8703e  Knock out every Component of the model to see what the circuit misses
    548ea61  Take the independent reviews: one Component spelling, stated exclusions and ranks

**`--knockout-completeness-sweep`** runs ticket 07's `knock_out_groups` with one-member groups over every head and MLP block of the model, on the causal sample. It does not run the circuit's singles separately. They are read out of the same forwards through `Effects.restrict`, so `knockout.json` and `sweep.json` share one clean and one corrupt pass per batch. The two files agree to the bit by construction. A CLI-seam test shows `knockout.json` is identical with and without the flag.

- **`knockout/sweep.json`** ranks all 1056 Components by |drop|, strongest first. Each row has `label`, `in_circuit`, `mean_drop` (positive helps deception), `standard_error`, `z`, `accuracy`, `rank`, `signed_rank` (knockout's own rule), `clears_threshold`, `flagged` and `kv_group`. It also carries the clean run, the instance ids, `threshold_counts` at 0.02, 0.05, 0.1 and 0.2, the 10 strongest outside the circuit, a `cost` block, and (from `548ea61`) `excludes`, `threshold_justification` and `head_table_columns`.
- **`knockout/sweep.png`** is its twin. It draws the 40 strongest by |drop| with circuit bars in dark orange and bold ticks, and dotted lines at plus and minus the threshold.
- **Head-table columns**, on circuit rows only: `knockout.sweep_rank` (rank by |drop| over the whole model) and `knockout.sweep_clears_threshold`. Both declare coverage over the causal sample. Components outside the circuit never become rows, even at threshold 0, and a test checks that.
- **`--knockout-sweep-threshold`** has a default of **0.1 logits**. It is a cut on |drop| in logits, not a fraction of the gap. The justification: it is about twice the standard error of the circuit's strong Components (0.03 to 0.07). It is about 3% of the 3.26 clean-minus-corrupt gap. And it is cleared by the circuit's top four on ticket 07's numbers.
- **1056, not 1057.** The embedding is excluded. Interchange-ablating it is the same as running the corrupt prompt, so it is not a Component knockout. The path-patching sweep counts it as a sender, which is why that sweep has one more entry.
- **`--dry-run`** prints the sweep line, `1056 x 13 batches (+2 shared) = 13754 forward pass(es), about 43.6 min on an A40`. It notes that the singles come from the same forwards, and it writes nothing of the analysis (tested).
- **`review.knockout_sweep_view`** is an additive view. It also has one line in `scripts/check_cell.py` and one notebook cell.

### Files touched

- **Owned:** `component_analysis/knockout.py`, new `tests/test_knockout_sweep.py` (21 tests, both envs), and additions to `tests/test_knockout_model.py` (7 tests, nnsight 0.7.0).
- **Shared, additive:** `component_analysis/review.py` (one new view), `scripts/check_cell.py` (one line), `review_components.ipynb` (one cell after the family knockout cell), `README.md` (layout line, cost sentence, stale-`sweep.json` warning), `docs/component-roles.md` (one paragraph after ticket 09's sweep note).
- **Not touched:** `analyze_components.py`, `registry.py`, `hooks.py`, `head_table.py`, `dataloaders.py`, the sbatch and `path_patching.py`. `knockout.py` imports `path_patching.label` so both sweeps spell a Component the same way. If ticket 14 renamed that function, the import breaks at load time rather than silently.

### Tests

| env | baseline on `4ba2877` | final on `548ea61` | new failures |
|---|---|---|---|
| login-node base (py3.9, BLAS pins) | 8 failed, 964 passed, 44 skipped | 8 failed, 985 passed, 44 skipped | none, the same 8 names |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 1092 passed, 19 skipped | 8 failed, 1120 passed, 19 skipped | none, the same 8 names |

Failure lists were diffed by name. They are all in `test_benchmarks.py`, `test_deception_common.py` and `test_deception_tasks.py`.

A mutation check bit as intended. Dropping one Component from the sweep list, or making `restrict` read the wrong key, fails 7 tests. Those include the equality test (`==`, not approx) and the coverage test. No `core.*` dump appeared.

### The Slurm run: job 22874364

| | |
|---|---|
| partition / node | `gpuA100x8` / gpuc02, one A100. Submitted to `gpuA100x8,gpuA100x4,gpuA40x4`; it started at once. |
| account | `bgrb-delta-gpu` (`sbatch --test-only` gave beto 4 days and bimc or bgrb the next day on A40) |
| `--time` | `01:30:00`, on the command line, rehearsed with `--dry-run` first |
| elapsed | **23:03**, `COMPLETED`; no error or traceback in `logs/analyze_components_22874364.out` |
| code | `bd8703e`. The review fixes landed 8 minutes after the start and change no number (see below). |
| output | `outputs/_analyses/ca15-knockout-sweep/delta__head/sdr/` (not committed) |

Command, from the worktree root:

    sbatch --account=bgrb-delta-gpu --time=01:30:00 --partition=gpuA100x8,gpuA100x4,gpuA40x4 \
      scripts/analyze_components.sbatch \
      --circuit sdr=outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414 \
      --circuit honest_c=outputs/llama-8b-instruct_sdr/nls0.3_honest_noedge_260819-083525 \
      --reference honest=outputs/llama-8b-instruct_sdr/nls0.3_honest_noedge_260819-083525 \
      --expr 'delta=sdr \ honest_c' --compose-granularity head \
      --task-from outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414 \
      --analyses knockout --knockout-completeness-sweep --suite-name ca15-knockout-sweep

**Bit-identity.** All 18 circuit rows of `sweep.json` equal `knockout.json` from the same job with `==`, on `mean_drop`, `standard_error`, `accuracy`, `knocked_logit_difference` and `n`. The instance ids are identical to each other and to the cell of record's 100.

This job ran on an **A100** and the cell of record (`sdr-first-run`, job 22240028) on an **A40**, so the cross-job comparison is cross-card. The clean run is +1.6566 here against +1.6132 there, and the largest single-drop difference is 0.023. This is the cross-card bf16 floor ticket 09 documented, not a regression. The 18 rows keep the record's order except near zero.

**Calibration.**

| | estimate (dry run, A40 constant) | measured (A100) |
|---|---|---|
| forwards | 13754 | 13754 (13 batches x 1058) |
| seconds per forward | 0.19 | **0.0944** |
| sweep wall time | 43.6 min | **21.7 min** (1299 s) |

The A100 ran at half the A40 constant, which matches ticket 09's "an A100 is roughly twice an A40". So the dry-run estimate is an upper bound on an A100. On an A40, expect it to under-predict by about 9%: ticket 09's sweep ran at 0.207 s per forward. Model load and the rest of the job took about 84 s.

**The top ten by |drop|** (all outside the circuit; positive drop helps deception):

| rank | Component | drop | SE | z | accuracy |
|---|---|---|---|---|---|
| 1 | `mlp.0.0` | **+3.1163** | 0.1239 | 25.1 | **0.01** |
| 2 | `head.17.24` | +1.3197 | 0.0528 | 25.0 | 0.72 |
| 3 | `head.20.14` | **−0.9956** | 0.0532 | −18.7 | 1.00 |
| 4 | `head.10.1` | +0.8821 | 0.0794 | 11.1 | 0.82 |
| 5 | `head.15.8` | +0.8716 | 0.0758 | 11.5 | 0.76 |
| 6 | `head.18.22` | −0.7957 | 0.0365 | −21.8 | 1.00 |
| 7 | `head.14.4` | +0.6901 | 0.0529 | 13.1 | 0.91 |
| 8 | `head.24.27` | +0.6249 | 0.0244 | 25.6 | 0.99 |
| 9 | `head.13.18` | +0.6243 | 0.0738 | 8.5 | 0.84 |
| 10 | `head.13.20` | +0.6089 | 0.0467 | 13.0 | 0.96 |

The circuit's strongest member, `head.17.25` (+0.4544), ranks **20th**, and `mlp.31.0` ranks 32nd. The others are `head.5.11` 71, `head.14.22` 93, `head.14.7` 95 (−0.104), then 120 and below. Five circuit Components clear 0.1.

**Non-circuit Components clearing 0.1: 90.** `threshold_counts` gives the rest:

| threshold (logits) | outside the circuit | in the circuit |
|---|---|---|
| 0.02 | 207 | 12 |
| 0.05 | 134 | 7 |
| 0.1 | 90 | 5 |
| 0.2 | 51 | 2 |

The flagged 90 are spread over the model but dense in layers 10 to 19, which hold 51 of them. That overlaps the 12-to-15 band the pre-registered hypothesis gives to selection; the circuit has five heads in layers 10 to 19 (L13H17, L14H7, L14H21, L14H22, L17H25). All 90 are in `sweep.json` `flagged`.

**Against the path-patching sweep's seven:**

| Component | path-patching direct effect (old sign) | knockout drop | knockout rank | clears 0.1 |
|---|---|---|---|---|
| `head.17.24` | −0.0575 | **+1.3197** | 2 | yes |
| `mlp.30.0` | +0.1275 | −0.4762 | 17 | yes |
| `head.30.24` | −0.0587 | +0.1892 | 58 | yes |
| `head.31.0` | −0.0809 | +0.1616 | 63 | yes |
| `head.27.7` | −0.0526 | +0.1075 | 92 | yes |
| `head.30.12` | −0.0543 | +0.0750 | 114 | no |
| `mlp.29.0` | +0.0937 | −0.0650 | 124 | no |

**Five of the seven clear 0.1. All seven agree in direction**: a negative old-sign direct effect pairs with a positive drop, and that pairing means helps deception under both conventions. The two that miss (`head.30.12`, `mlp.29.0`) clear 0.05.

The overlap is narrow in the other direction. Only `head.17.24` is near the top of both lists. The knockout top ten is mid-layer heads and `mlp.0.0`, which have little direct effect on the Readout. So these Components matter through what they feed downstream, which the direct-effect sweep cannot see.

`head.17.24` shares KV group 6 of layer 17 with circuit head L17H25, and its knockout is about three times L17H25's. Path-patching numbers are from job 22240068 (64 instances, A40). The `component-analysis` tip now carries ticket 14's flipped sign, under which those numbers are positive.

### What the review changed

Both axes ran as independent sub-agents. Their handbacks failed and their reports came by message, forwarded with calls by the orchestrator. The report is at `reports/15-knockout-completeness-sweep-review.md`.

- **Standards.** No documented standard was broken; there were seven judgement calls.
  - Fixed: one label function (path patching's), so `sweep.png` and its twin spell a Component the same way; the circuit-only charts keep `L17 H25` under `_short_label`. Also fixed: `scheme_of` and `sweeping` helpers, a `sweep_threshold` docstring, the sweep columns returned rather than mutated in, the `top` parameter made a constant, and one forward count (1056 + 2 = 1058) everywhere.
  - Kept by ruling: `kv_group`, and the circuit, task and threshold argument clump.
- **Spec.** It matched the ticket with nothing blocking.
  - Fixed: `sweep.json` now states the embedding exclusion, how `sweep_rank` differs from `knockout.rank`, and the threshold's justification. `docs/component-roles.md` has the same note. The README warns that a rerun without the flag leaves the old `sweep.json` on disk.
  - Kept by ruling: the extras (threshold ladder, `z`, `strongest_outside_circuit`, notebook cell, check_cell line).
- **Effect on the job's outputs.** The job ran on `bd8703e`, so its `sweep.json` lacks the three new meta fields and its PNG ticks read `L17 H25`. No number differs, so by the orchestrator's ruling it was not rerun.

**The threshold flag is not a significance test** (Spec finding 4). It is a fixed cut on |mean_drop| over 1056 Components, calibrated on SDR nls0.3 only. A weak head with a large standard error can clear it at z about 1.4. Each row's `z` and the `threshold_counts` ladder are the mitigation. On this run every one of the top 50 has |z| of at least 4.0, and only 1 of the 90 flagged has |z| below 3 (the lowest is 2.4).

### Open questions for the researcher

1. **The threshold default.** At 0.1 logits the flag lists 90 Components outside the circuit, so it is not selective at the scale of the whole model. Two options: raise the default (0.2 gives 51, 0.5 gives 13), or add a z gate. A gate of |z| ≥ 3 alongside the cut would remove only 1 of the 90 here, so the cut is what decides. Both are one line. The ladder in `sweep.json` lets a cut be chosen without a rerun.
2. **Significance gating.** Should `flagged` require |z| above a bar in addition to |drop|?
3. **`mlp.0.0`.** Its knockout removes almost the whole gap (+3.12 of a 1.66 clean margin, accuracy 0.01). Layer-0 MLP behaves like a second embedding: interchanging it rewrites the corrupted token's representation, much as the embedding exclusion does. Read it as a positive control rather than a Component the pruning missed. Should it be excluded like the embedding, or kept and marked?
4. **The circuit is far from complete on knockout.** Its best member ranks 20th, and mid-layer heads in layers 10 to 20 dominate the top of the list. This adds to the seven-from-path-patching evidence that the head-granularity delta is incomplete. The researcher's 2026-10-13 decision says to leave that as evidence, and nothing here changes the circuit.
