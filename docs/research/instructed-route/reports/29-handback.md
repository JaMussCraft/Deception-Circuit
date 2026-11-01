# Hand-back 29: why the ser smoke failed gate G3 on the summed O

Agent: ticket implementer (Claude Opus 5.5), session claude-230e4716. Task: the lead's request to diagnose the G3 sum miss of the B1 smoke, Bridges-2 job 50105613, on CPU from the fetched JSON. Status: resolved (diagnosis and recommendation; no code changed).

## What changed

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/29-handback.md`, this file.

No other file was edited. The smoke JSON files, `results/b1-smoke/` and the code were only read. The analysis scripts sit in the job's temporary directory, which is deleted with the job, so the numbers below are the record.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python /u/swong2/.claude/jobs/230e4716/tmp/g3_diag.py
/u/swong2/.conda/envs/mgnp/bin/python /u/swong2/.claude/jobs/230e4716/tmp/g3_diag2.py
```

Both read `outputs/_analyses/instructed-route-b1/smoke/{far,ser}/Ct__leaf/{far,ser}_v2/route_closure/route_closure.json` and `docs/research/instructed-route/results/b1-smoke/b1_readings.json`. They compare the forward and offline estimators sender by sender and instance by instance, and against the joint swap.

### Finding 1: the 0.25 comes from the T arm, mostly from one instance, and builds up over hundreds of senders

The smoke ran one batch per task (`route_max_batches` 1, 8 ids), so the only batch is the one at fault. On ser:

| arm | forward O | offline O | difference |
|---|---|---|---|
| T | 1.0330 | 0.7805 | 0.2525 |
| dq_all | 0.4277 | 0.3684 | 0.0593 |

The gate reports the larger of the two, the T arm. Within it, instance `0141c4706c53` (G 10.67) gives 0.154 of the 0.2525. Instances `012e62b89f5c`, `019507afa963` and `04604f535e45` give about 0.04 each, and `01ef48baaaca` gives −0.032.

**The cause is many small same-sign errors.** On ser T, 81% of the 978 per-sender differences are positive. Their mean is 2.6e-4 against a standard deviation of 3.0e-4, in units of G.

| largest senders by error | signed sum of their errors |
|---|---|
| 10 | 0.011 |
| 100 | 0.083 |
| 300 | 0.181 |
| all 978 | 0.2525 |

The error is spread over every layer bucket. Heads in layers 8 to 23 give 0.08 per bucket.

Within one instance the error has one sign. On `0141c4706c53` every outside sender carries about 0.0065 logits too much. Across instances the sign changes.

**A few large senders are not the cause.** The largest single error is 0.0013, at `head.24.14`.

**An accounting difference is not the cause.** The two estimators sum the same 978 senders, and the in-sum sets are identical in both arms. Neither includes the embedding or C_t, and the per-sender sum of differences equals the difference in O exactly.

### Finding 2: the forward estimator is the inaccurate one

The two estimators compute the same quantity in exact arithmetic; ticket 5's fp32 tiny-model test has them agree to 1e-6. Here they agree to 5e-4 on the joint swap of all outside senders at once.

Each estimator's per-instance sum of single swaps can be compared with that joint swap. The sum differs from the joint swap for a real reason, the nonlinearity of the final norm. But the offline sums stay close to the joint swap, and the forward sums do not:

| task, arm | RMS of forward sum minus joint (logits) | RMS of offline sum minus joint (logits) |
|---|---|---|
| ser, T | 2.54 | 0.21 |
| ser, dq_all | 0.885 | 0.097 |
| far, T | 2.27 | 0.86 |
| far, dq_all | 0.584 | 0.156 |

On `0141c4706c53` the forward sum is 15.94, the offline sum 9.55 and the joint swap 9.46.

**The forward estimator works in bf16.** For each sender it rebuilds the whole residual stream in bf16 with one small change, so that change is rounded at every later bf16 addition and at the final norm's input. The offline estimator applies the same change to the captured residual in fp32.

**Why the errors share a sign within an instance is not verified.** The JSON holds no residuals. A likely cause is that each instance's errors round against the same few large residual elements, which also set the RMS scale.

**Senders that do not change contribute exactly zero.** Under dq_all, senders in layers 0 to 16 have equal values in D and D_q. Their forward drop is exactly 0.0, so the frozen forward reproduces m(D) bit for bit. The error comes only from senders whose value changes.

### Finding 3: far has the same per-instance error and passed by cancellation

Far's per-instance forward errors are as large as ser's. One instance is off by 3.77 logits, and the RMS against the joint swap is 2.27. Far's per-instance shares of the O difference run from −0.043 to +0.026, so they cancel to −0.0125. Ser's mostly share a sign, so they add to 0.2525. Far passed the gate by cancellation, not because its forward sum is accurate.

### Finding 4: the readings use the forward estimator, and the estimator could decide ser's verdict

`t1.summary.rule_estimator` is "forward", and `scripts/route_closure_readings.py` uses the forward estimator whenever it ran. So O, O_q, M_q and the closes-or-bypass verdict come from the forward sums. Only R1's label compares the offline M_q against the offline controls.

| task | forward M_q | offline M_q | verdict |
|---|---|---|---|
| far | 0.376 | 0.369 | bypass |
| ser | 0.414 | 0.472 | bypass |

These are 8-id smoke values.

**The verdict could flip.** At 100 ids the forward error shrinks only with the square root of n where its sign varies. If it has a mean sign, as on ser here, it does not shrink at all. A gap of 0.03 to 0.06 in M_q between the estimators is plausible at 100 ids. Ser's offline M_q is already within 0.03 of 0.50, so ser's verdict could depend on which estimator is the rule of record.

**The label is unlikely to change.** M_C3 is −0.02 on far and −0.04 on ser. The C1 and C2 draws reach at most 0.20, far below any M_q near 0.5. If the loop closes, the label is route-specific under either estimator.

### Finding 5: the gate is at the right scale and caught a real problem

- **The per-sender check (0.01) cannot see this bias.** The observed per-sender differences are 0.0006 to 0.0013, about ten times below the tolerance, and a bias of 3e-4 per sender is invisible one sender at a time.
- **The joint-swap check cannot see it either.** One large change is barely affected by rounding, so the joint swap agrees to 5e-4.
- **Only the sum check tests the rule number.** The rule number is a sum of about 980 single swaps, and only the sum check tests that sum.
- **The tolerance is about right.** With O between 0.75 and 1.0, an error of 0.02 in O moves M_q by 0.01 to 0.03, which is the precision a verdict at 0.50 needs.

Loosening the gate would hide the problem rather than settle it.

## Execution evidence

- **Job and cluster.** Bridges-2 job 50105613 on host w003, from both cells' `run_manifest.json`. This analysis ran locally on the login node with the two commands above.
- **Exit code or Slurm state.** Not checked by me. Both cells wrote a complete `route_closure.json` with every gate field.
- **Row counts.** Each task has 8 instances against the 8 expected for one batch. Far has 984 outside senders (72 in the grid) and ser has 978 (78 in the grid). The forward and offline in-sum counts are equal in every arm.
- **Baseline reproduces.** G1 is bit-identical on both tasks and G2's maximum difference is 0.0, as the gate fields record.
- **Provenance.** Both `outputs/_analyses/instructed-route-b1/smoke/{far,ser}/Ct__leaf/{far,ser}_v2/run_manifest.json` name commit `476c18770bcd3d461368ce67faeb535e45b29270`.

Findings 1 to 5 are numbers read off these files. The bf16 mechanism in finding 2 is not yet verified, because no residuals were saved.

## What is NOT done

- **The rounding mechanism was not confirmed.** That would need the 8B model to rerun one instance's forward sweep in fp32, or to save the final residuals.
- **No code was changed.** That includes the readings script and the gate.
- **No ruling was drafted into `spec.md`.**

## Open questions

1. **Which estimator is the rule of record for O, O_q and M_q?** I recommend the offline estimator, recorded as a pre-run ruling in `spec.md` before either 100-id task job runs. The reasons:
   - it is the same quantity computed in fp32;
   - its sums track the joint swap that both estimators agree on;
   - it is already the estimator R1's label uses, so verdict and label would rest on one estimator;
   - the forward numbers would stay in the JSON and the readings as a reported comparison.

   This is a change from plan 1.2, which named the forward sweep. No 100-id data has been read, so it is a clean pre-run change. Default: adopt it.
2. **How should the readings script follow the ruling?** It needs a flag choosing the rule estimator, defaulting to offline, plus a test at the two estimators and a rerun on both interpreters. That is about 30 minutes, with no GPU and no change to `route_closure.py`. Default: make that change before the task jobs finish.
3. **How should G3 be reported under the ruling?** Record ser's smoke miss as failed and explained. At 100 ids, report G3 as computed, together with the per-instance RMS of each estimator's sum against the joint swap. Default: keep the gate unchanged and do not loosen it.
4. **Should the task jobs keep the forward sweep?** Dropping it with `--route-sweep offline` saves about 25,000 forwards, about 20 minutes per task on an H100. But it also loses the G3 comparison at 100 ids. Default: keep it; the reservations already include it.
5. **Should the gate miss block the task jobs?** No change to the job or to `route_closure.py` is needed, since the job already writes both estimators. Default: submit the far and ser task jobs as written, and settle questions 1 and 2 before anyone reads the 100-id numbers.
