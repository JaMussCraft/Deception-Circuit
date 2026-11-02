# Hand-back ticket 95: Unit E scoped closure complete

Agent: independent Codex reviewer. Ticket: Unit E report95 B2 final closure. Status: handed-back.

## What changed

**Disposition: the residual B2 blocker closes. No blocker remains from the scoped B1–B4 review.** The prior closure accepted B1/B3/B4 and identified the terminal-entry lineage defect; this pass inspected only its fix and related behavior. No implementation or repository test was edited, and the author report was not read.

The updated loop at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_direction_workload.py:972` examines every ledger entry before computing the linked set. If either the admission ID or digest matches the immutable original, both must match. A contradictory same-ID digest or same-digest ID now rejects in every job state; it cannot disappear from the consumed-reservation set. Matching entries still require exact envelope membership and full source/inventory/ceiling/reservation lineage before their reserved hours are summed.

The independent residual probes cover the original completed/failed cases, running/reserved variants, reversed ID conflicts, consistently linked omissions, and included reservations that exhaust the envelope. They all reject. A valid original anchor, an unrelated distinct admission charged globally, and a matching current running reservation still pass. The current reservation is charged once and contributes no additional reservation charge. Source: `report95-b2-round2-probes-mgnp.log` and `report95-b2-round2-probes-base.log`. No new breakage was found within this narrow change.

Review files for the orchestrator:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-direction-workload-closure-handback.md` — updated independent closure report.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-direction-workload-closure-round1-handback.md` — preserved prior closure report with the original residual defect.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-b2-round2-probes.py` — independent narrow closure script.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-b2-round2-probes-mgnp.log` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-b2-round2-probes-base.log` — byte-identical independent outputs.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-b2-round2-tests-mgnp.log` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-b2-round2-tests-base.log` — direct focused test output.

Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/`, with the same filenames. Earlier scripts/logs and the initial review remain unchanged. No git or apply operation was used.

## How verified

All commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_workload.py -k 'envelope or lineage or reservation or reserved or postfit or failed_attempt' -p no:cacheprovider -q > /tmp/report95-b2-round2-tests-mgnp.log
```

Observed: 32 passed, 63 deselected, in 39.57 seconds; exit successfully. Source: `report95-b2-round2-tests-mgnp.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_workload.py -k 'envelope or lineage or reservation or reserved or postfit or failed_attempt' -p no:cacheprovider -q > /tmp/report95-b2-round2-tests-base.log
```

Observed: 32 passed, 63 deselected, in 44.19 seconds; exit successfully. Source: `report95-b2-round2-tests-base.log`. This is the independent selection actually run, not the author's supplied selection/count.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/report95_b2_round2.py > /tmp/report95-b2-round2-probes-mgnp.log
```

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 /tmp/report95_b2_round2.py > /tmp/report95-b2-round2-probes-base.log
```

Observed: both exit successfully, with 16 rejection cases and 3 valid boundary cases each. Sources: `report95-b2-round2-probes-mgnp.log`, `report95-b2-round2-probes-base.log`.

```bash
cmp /tmp/report95-b2-round2-probes-mgnp.log /tmp/report95-b2-round2-probes-base.log
sha256sum component_analysis/a3_direction_workload.py tests/test_a3_direction_workload.py
```

Observed: probe logs are byte-identical. Reviewed source digests are `4ad9b49c32c14e5f6ae44c3201cc1da1e250eeef22a9592f60907e823ce25d70` for the workload module and `642d9b58b9695ba98fcf66fcf437011071ae1e632b641cfd88b9756d997a15f7` for its tests. These identify reviewed file bytes, not a scientific execution source commit.

## Execution evidence

This review ran local CPU tests and pure synthetic probes only; it makes no scientific execution claim.

- Job/cluster: local commands above, with no scheduler job.
- Exit status: both focused test commands and both independent probe commands succeeded.
- Counts: 32/32 selected tests pass on each interpreter; independent probes cover 16 malformed/rejected cases and 3 valid cases each. Sources: `report95-b2-round2-tests-mgnp.log`, `report95-b2-round2-tests-base.log`, `report95-b2-round2-probes-mgnp.log`.
- Baseline comparison: identical selected-test passing counts and byte-identical probe outputs across the supported interpreters. This is a software/synthetic comparison, not a scientific baseline reproduction.
- Scientific `run_manifest.json` and scientific source commit: not applicable; no model, GPU, Slurm, API, checkpoint/weight or notebook execution occurred.

## What is NOT done

Closed B1/B3/B4 items were not reopened and no broad suite was run. No implementation fix, new repository test, reservation or forecast was performed by this reviewer.

Unit F runtime attestation remains deferred: the root reader must load original admissions/reservations and current ledger/capacity evidence from authoritative completed artifacts. Self-hashed dictionaries cannot authenticate their origin. Protocol geometry freezing and the separately reviewed conditional packed reuse adapter remain integration obligations. This closure accepts the pure consistency checks; proposals remain `execution_authorized=False`. No additional human approval gate is introduced.

## Open questions

None within the scoped closure. Default for the orchestrator: accept the B2 fix, retain the earlier B1/B3/B4 closure, and continue the separately scoped Unit F integration review.
