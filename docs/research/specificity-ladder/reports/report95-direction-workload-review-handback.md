# Hand-back ticket 95: Direction workload and admission review

Agent: independent Codex reviewer. Ticket: Unit E of the direction integration plan. Status: handed-back.

## What changed

Review disposition: **three blocking findings in Unit E; changes requested**. No implementation or repository test was edited. Author report88 was not read. The full integration plan, workload implementation/tests, runner capture/scoring/packing/positive-control structure, artifact publication contracts, and the selected metadata producer were inspected independently.

Review files for the orchestrator's explicit file list:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-direction-workload-review-handback.md` — this review.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-workload-probes.py` — independent pure adversarial probes and count oracle.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-probes-mgnp.log` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-probes-base.log` — probe outputs.

Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/`, with the same review/probe filenames and `report95-focused-tests.log`, which records the focused test tool-output excerpts. No apply operation is staged and no git command was run.

**B1 — target cache/host capacity is never admitted against the target inventory (high).** At `component_analysis/a3_direction_workload.py:667`–`691`, capacity is checked only against each measurement's self-reported pilot cache/peaks. No comparison uses the target's `bytes` forecasts. The serial probe admits a target whose capture payload alone is 912 bytes and projection blocks are 192 bytes, while every receipt reports cache capacity 1 byte and memory capacity 2 bytes. The maximum forecast byte field is 30456. A small validation cohort fitting is insufficient evidence that the full train/validation cache fits. Add independently derived full target host/disk/cache requirements and capacity checks for their storage tiers, including retained projections, source records/tokens, optional clause summaries and serialization payloads; keep measured GPU peak/capacity checks separate. Reconcile forecast quantities with what the accepted capture/publishing adapters actually retain. The current byte fields are useful but do not enforce admission.

**B2 — postfit envelope is not bound to an actual original reservation (high).** At `component_analysis/a3_direction_workload.py:731`–`750`, an empty `entry_ids` list passes, the ceiling is a self-hashed supplied number, and a listed entry need only have phase M2/subphase directions. Both an envelope with no ledger entries and an envelope naming an unrelated completed direction job with inventory digest consisting of 64 `f` characters are admitted. The probe log `report95-probes-mgnp.log` reports consumed 0.01 GPU-hours; the former reports zero. Neither establishes an original fit/validation reservation. The upper inventory and scientific row subset check do not supply this missing accounting link. Require a nonempty original reservation/admission lineage, bind its entries to the upper inventory/source and admitted ceiling, account for already consumed and still reserved pieces once, and constrain remaining requirements to the original unconsumed envelope. A caller-supplied enlarged envelope must not replace the original authorized bound. Global nine-hour/full-A3 checks are valuable but do not enforce this narrower condition.

**B3 — packed evidence accepts a missing dummy-lane experiment (medium, blocks packed admission contract).** At `component_analysis/a3_direction_workload.py:576`–`607`, `dummy_lanes_tested=True` is accepted while `scope.dummy_cells` may be empty. Removing every dummy cell and its comparison rows, then recomputing scope/receipt digests, still admits the packed proposal; the probe strips 98 evidence records. The accepted runner's producer explicitly performs a dedicated one-axis pass in each serial and packed geometry, even when the main panel divides exactly. Require the producer-derived dummy coverage for every eligible batch and its complete comparisons, alongside the existing full-tile/nonzero/map/axis checks. Do not permit a summary boolean to replace those observations. This proposal remains `execution_authorized=False`, so this finding does not describe authorized execution.

The small independent count oracle agrees with the frozen inventory; these derived counts are recorded in `report95-probes-mgnp.log`. With two mechanism IDs and two utility IDs in the injected fixture, `Q=10*2+2+2*2=26`; all remaining panels contain `9*((201*26)+(2*2*22)+(3*2*24)+(33*26))=56844` scientific recipient rows. Independently counting tile dispatch gives 1773 scoring tiles, each with five forwards, plus 432 singleton positive-control forwards. Train captures include four conditions and both streams without per-seed repetition. The runner's loop structure matches five forwards per scoring tile, three singleton forwards per positive calibration, and separate serial/packed/full/dummy equivalence passes.

Derived inventory counts from `report95-probes-mgnp.log`:

| Injected stage | Raw rows | Scoring shards | Capture chunks | Forward operations including warmup | Serialization publications |
| --- | ---: | ---: | ---: | ---: | ---: |
| prefit | 234 | 75 | 102 | 1639 | 251 |
| fit-select | 234 | 75 | 57 | 649 | 206 |
| selected-pilot | 56844 | 1035 | 468 | 150130 | 1577 |
| remaining | 56844 | 1773 | 66 | 9364 | 1985 |

These are synthetic inventory counts, not measured production runtimes or a forecast. The selected timing workload includes serial measurement of every actual frozen null axis; its large derived forward count must stay intact when M1 feasibility is evaluated.

Other reviewed boundaries (sources: `../plan-a3-direction-integration.md` and `../../../../component_analysis/a3_direction_workload.py`): the exact task/seed scope, 199 assessment and 32 calibration axes, both streams/all mechanism arms, IOI, both MMLU floors, learned/nuisance secondary controls, both-sign steering including random axis zero, positive/replay controls, deterministic short chunks, dummy/full physical tiles, per-job serialization/startup/finish costs, source/site/operation/profile matching and unmasked lengths are explicit. Reconstruction rejects caller-rehashed reduced totals. The largest matching sample and 1.25 buffer feed each job's walltime. Failed/completed entries charge actual spend; active matching reservation charges once. Direction M1 0.5, all-M1 2, direction M2 9, full A3 40 GPU-hours and the retained contingency are checked. Unfitted nuisance retains its conditional-unavailability receipt and obligations; no valid DOM for a seed blocks that task. Selected `inventory_identity` is consumed separately from scientific `selected.identity` as required by the new producer.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_workload.py -p no:cacheprovider -q
```

Observed: 64 passed in 70.97 seconds, exit 0. Source: `report95-focused-tests.log` (tool-output excerpts).

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_workload.py -p no:cacheprovider -q
```

Observed: 64 passed in 84.17 seconds, exit 0. Source: `report95-focused-tests.log` (tool-output excerpts).

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/report95_probes.py > /tmp/report95-probes-mgnp.log
```

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 /tmp/report95_probes.py > /tmp/report95-probes-base.log
```

Observed in both logs: capacity-underflow admission, empty/unreserved-envelope admission, stripped-dummy admission, unrelated-envelope-entry admission, and matching independent row/tile/positive-control arithmetic. The preserved script and probe logs listed above are exact copies of these temporary files. Both probe logs are byte-identical. Both handback copies pass `research-session lint`; the report-number checker was run and its listed quantities were traced to these logs, the independent arithmetic, or the integration plan.

## Execution evidence

This review ran local CPU tests and pure Python probes only. No scientific or model execution result is claimed.

- Job/cluster: local commands above; no scheduler job.
- Exit codes (sources: `report95-focused-tests.log`, `report95-probes-mgnp.log`): both focused pytest commands and both probe commands exit 0.
- Counts against expected (derived from `report95-probes-mgnp.log` and `report95-focused-tests.log`): 64/64 focused tests on each interpreter; independent remaining-panel oracle 56844/56844 rows, 1773/1773 scoring tiles, 432/432 positive forwards. Each of the four malformed-admission probes prints `admitted: true` in both environments.
- Baseline comparison (source: `report95-focused-tests.log`): identical 64-test passing counts and identical pure probe/count outputs across the two supported interpreters; this is a software/synthetic comparison, not a scientific baseline reproduction.
- Scientific provenance `run_manifest.json` and full scientific source commit: not applicable; no model run, checkpoint, model weight, GPU/Slurm/API access or notebook execution occurred.

## What is NOT done

No implementation fixes, new repository tests, broad suite, real timing/pilot measurement, source publication, reservation or forecast was performed. Unit E is not accepted until B1–B3 have targeted fixes and independent regression checks.

Deferred Unit F integration follows `../plan-a3-direction-integration.md` and is distinct from these blockers: canonical protocol must freeze the actual workload geometry, utility/timing memberships and cache/shard layouts; timing producer must publish byte-checked complete validation-only measurement receipts linked to the independently reconstructed target inventory; live readers must enforce source/model/site/operation/donor/physical geometry and root ledger provenance; final execution requires root RS reservation and fresh access checks. The root reuse ruling allows conditional proposals for independent fixed target rows under identical execution assumptions; it does not say the target rows were measured. Prefit timing admits only fitting/validation, while selected timing must exercise all 199 actual frozen null axes. Packed execution remains unavailable until the separately reviewed reuse adapter exists. Nothing here introduces another human approval gate.

## Open questions

For the orchestrator: route B1–B3 to the Unit E owner, defaulting to changes requested and retaining the complete workload. Keep Unit F production dispatch deferred until its own review; do not shrink axes/rows or reuse another phase's budget to make admission fit. No human scientific decision is needed to implement these contract checks.
