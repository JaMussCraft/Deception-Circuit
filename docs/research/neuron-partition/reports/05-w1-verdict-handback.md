# Hand-back 05: W1, the item-10 verdict script (N1 and N2)

Agent: implementation worker W1 (Claude, Opus). Ticket: the orchestrator's brief "New task: the verdict script for
item 10 (N1 and N2 bars)". Status: resolved. The code, the synthetic tests and the check against W2's pilot cell all pass on
both interpreters.

## What changed

The orchestrator commits these from the worktree. Both files are new, and no other file was edited.

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/scripts/neuron_partition_verdict.py`
  reads one or more cells written by `scripts/neuron_set_ablation.py` (`--cell DIR`, repeatable, one per k). It
  recomputes every number from the per-id lines of `rows.jsonl`, mirroring W2's definitions: streams are averaged
  within an id, then ids are averaged.
  - **Effects.** Per set, reference and id subset (the whole sample, half 1 and half 2), it computes D and I removed
    by the ladder margin ratio (R2, primary) and by the rate at margin 0.7 (R8). Under mean and zero, the rate
    compares ablated D with ablated H; under twin, it compares ablated D with the intact twin.
  - **Guard.** The epsilon guard is `max(1e-6, 10 × self_replay_error)` from the cell's `summary.json`, as W2 sets
    it.
  - **Collateral.** H, F and IOI argmax accuracy shifts are in points and come from the mean reference for every
    reference (R7). D's deceptive-rate change is in points.
  - **Nulls.** Each metric has a matched-null distribution over the `null_<class>_<k>_<i>` groups, on the same ids,
    with its per-null values and its 5th, 50th and 95th percentiles.
  - **N1 bars.** Each bar records `passed`, `value` and a `reason` when no value exists; a missing value fails its
    bar. The N1 pass is read on D_only and needs every bar under twin and mean on the whole sample and both halves
    (mean and zero if there are no twin cells). A lead is a (reference, subset) that meets every bar without the
    whole pass.
  - **N2.** For H_only, the verdict is bypass, suppression or shared, or undetermined. The mean reference decides,
    zero is beside it, and twin is the descriptive reverse patch.
  - **Bootstrap.** 1,000 resamples of ids, seed 2, give 2.5th and 97.5th percentiles for D and I removed, by margin
    and by rate.
  - **Outputs.** It writes `verdict.json` (results keyed reference, class, k, subset; plus `definitions`, `choices`,
    the input hashes and the N1 summary) and `verdict.md` (one table per reference, then the N1 and N2 tables).
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/tests/test_neuron_partition_verdict.py`
  holds 21 tests. A synthetic cell is written in W2's exact `rows.jsonl` and `summary.json` schema.

**Halves (R10).** W3's rule is recoverable, and the script uses it. `split_halves` from
`scripts/neuron_partition_data.py`, stratified by `pressure_id` with seed 2, is applied to the union of the sample's
D and I ids. `pressure_id` is read from the far_v2 and I-pool test splits. H and F take their D id's half, and N its
I id's half. IOI is not in the sample, so all IOI rows enter both halves. If the records cannot be read, the fallback
is a seeded shuffle of the sorted ids, alternated, and the method used is recorded in `verdict.json`.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q -rs tests/test_neuron_partition_verdict.py --basetemp=/projects/beto/swong2/.w1-5201d56c-tmp/bt_v1
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q -rs tests/test_neuron_partition_verdict.py --basetemp=/projects/beto/swong2/.w1-5201d56c-tmp/bt_v2
```

Observed: `20 passed, 1 skipped` on mgnp and on base. The skip is the real-cell test ("no real ablation cell yet").
The temp directories are under `/projects`, per the orchestrator's quota note. The tests check:

- **Designed numbers.** D removed 0.6, I removed 0.1, D rate removed 1.0, I rate removed 0.0, and null p95 equal to
  numpy's 95th percentile of the 20 nulls. Every bar passes under all three references on all three subsets, and the
  N1 summary passes at k 500.
- **Each bar fails alone.** Size 2,500, D removed 0.4, I removed 0.4, H, F and IOI each shifted 10 points, and nulls
  above the tested set each fail only their own bar.
- **Epsilon.** A gap at or below epsilon gives no D removed and fails its bar with the reason.
- **Leads.** A set that passes on half 1 but not on the whole sample is a lead, not a pass.
- **N2.** Bypass, suppression or shared, and undetermined each come out where expected. A null that also drops H
  makes the verdict undetermined.
- **Naming.** k is read from the null names and from a `<class>_<k>` suffix.
- **Agreement with W2.** On a noisy synthetic cell, the array metrics equal W2's own `ladder_ratio`, `share` and
  `removed_fraction` under twin and mean.
- **Bootstrap.** It is reproducible by seed, and its interval brackets the point estimate.
- **Halves.** `split_halves` on the rank ids with train and validation `pressure_id` reproduces `far_rank_ids.json`
  `halves.A` exactly. On the real seed-2 sample, the rule (not the fallback) runs, the union splits within one, and
  D and I each split 300.
- **CLI.** It writes `verdict.json` and `verdict.md` with the expected keys and tables.

## Execution evidence

W2's pilot cell `outputs/_analyses/neuron-partition/ablation/pilot-e5962fe/` finished at 12:09 pm CST. It holds
D_only (219 neurons) and DI_shared (281) at k 500, each with 20 nulls, under twin, mean and zero. It has 16 ids per
condition and 100 IOI rows, and its self-replay error is 0.0 for D and I.

- **Real-cell test.** The test file was rerun with the cell present.

  ```
  /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q -rs tests/test_neuron_partition_verdict.py --basetemp=/projects/beto/swong2/.w1-5201d56c-tmp/bt_v3
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q -rs tests/test_neuron_partition_verdict.py --basetemp=/projects/beto/swong2/.w1-5201d56c-tmp/bt_v4
  ```

  Observed: `21 passed` on both, with no skips. For every set, reference and condition, the real-cell test
  reproduced the cell's own `summary.json` to 1e-9: the whole-sample D and I removed (margin and rate) and the H, F,
  IOI and N collateral shifts.
- **Verdict on the pilot.** It ran in 4 s and wrote to
  `outputs/_analyses/neuron-partition/verdict/pilot-e5962fe/`, as `verdict.json` and `verdict.md`.

  ```
  /u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_verdict.py --cell outputs/_analyses/neuron-partition/ablation/pilot-e5962fe --output-dir outputs/_analyses/neuron-partition/verdict/pilot-e5962fe
  ```

  The halves came from the rule, not the fallback. Of the sample's D ids, 156 fall in half 1 and 144 in half 2; of
  the I ids, 141 and 159. On the pilot's 16 ids per condition, the halves hold about 8 ids each.
- **Pilot readings.** These come from 16 ids and are a smoke test of the script, not the item-10 verdict. The
  brackets are bootstrap 95% intervals, and the shifts are in accuracy points.

  | Reference | Class | D removed, margin | I removed, margin | IOI shift |
  |---|---|---|---|---|
  | twin | D_only | 0.327 [0.29, 0.37] | 0.194 | −9.0 |
  | mean | D_only | 0.264 | 0.140 | −9.0 |
  | twin | DI_shared | 0.440 | 0.501 | −12.0 |

  - The null 95th percentile of D removed is about 0.01 to 0.02 under every reference, and the H and F shifts are
    0.0.
  - N1 fails at k 500 on every subset, on two bars: D removed is under 0.50, and the IOI shift is 5 points or more.

## What is NOT done

- **The item-10 verdict.** The full cells, with all four classes at k 500, 1,000 and 2,000 on the 300-id sample,
  have not run. The pilot output is a check of the script, not the verdict.
- **Interpretation.** No reading is recorded as a finding.

## Open questions

- **N2 null rule.** "The matched null moves H accuracy under 5 points" is read as the 95th percentile of |null H
  shift| < 5. Default: that rule. The alternative is the null's mean shift.
- **D's deceptive-rate change for N2.** It is p(m_D ≥ 0.7), ablated minus intact, on D's ids under the same
  reference. Default: that.
- **Zero reference.** It enters N1 only when there are no twin cells, as the "twin wiring never lands" clause of item
  10 allows. Otherwise it is reported beside the others. Default: that.
