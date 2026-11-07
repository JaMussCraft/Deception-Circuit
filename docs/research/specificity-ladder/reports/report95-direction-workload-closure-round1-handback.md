# Hand-back ticket 95: Scoped Unit E closure review

Agent: independent Codex reviewer. Ticket: Unit E report95 closure of B1–B4. Status: handed-back.

## What changed

**Disposition: B1, B3 and B4 close within this scoped review; B2 retains one blocking lineage-accounting defect.** No implementation or repository test was edited. The author report was not read. Review covered only the changed storage admission, original-envelope lineage, dummy-experiment coverage, reservation accounting, their tests, and the corresponding accepted runner payload/producer contracts.

Review files for the orchestrator, mirrored under the primary direction directory:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-direction-workload-closure-handback.md` — this scoped closure review.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-closure-probes.py` — independent closure and adversarial probes.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-closure-probes-mgnp.log` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-closure-probes-base.log` — byte-identical probe outputs.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-closure-tests-mgnp.log` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report95-closure-tests-base.log` — direct focused pytest output.

Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/`, with these same filenames. The original review remains unchanged. No apply operation or git command was used.

**Residual B2, high: conflicting admission digest hides terminal consumption from the fit envelope.** In `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_direction_workload.py:972`, `linked_ids` selects entries solely by matching `reservation_lineage.admission_sha256`. An entry carrying the original admission ID but a conflicting digest falls outside that set; if it is omitted from `envelope.entry_ids`, the later lineage checks never inspect it. For terminal entries the active-matching guard does not recover this omission.

The independent repro starts from a valid anchored postfit fixture. Its original envelope ceiling is 0.5 GPU-hours and the completed capture reserves 0.1. A later completed or failed attempt reserves 0.49, reports actual 0.001, and names the same original admission ID. Its lineage digest is consistently recomputed after changing only the referenced admission digest; the later entry is present in the ledger and expected-entry manifest, but omitted from the envelope. Both cases are admitted, reporting `all_reserved=0.59` and `envelope_consumed=0.1`. Thus globally charged reservations already exceed the original fit envelope while another proposal is accepted under that envelope. These derived probe quantities and both terminal states are recorded in `report95-closure-probes-mgnp.log` and `report95-closure-probes-base.log`.

A correctly linked omitted attempt rejects. The analogous running/reserved cases reject through the current-inventory active guard. The remaining defect is specifically completed/failed consumption with a contradictory reference to the same immutable admission. Reject any same-admission-ID conflicting digest before selecting or summing the linked set; validate that both the ID and digest identify the same original admission. Add terminal-state regression cases. This is a continuation of B2, not a broader new review topic.

**B1 closes within scope.** Full target host, cache, output and scratch requirements are independently reconstructed, including source records/tokens, optional clause summaries, projection/fit/axis payloads, complete result/control rows, metadata and temporary publication. Measured host peak is added to host retention. Pool identities aggregate tiers sharing a physical capacity. The updated fixture helper now supplies adequate capacity; the independent script explicitly forces each storage tier to one byte and separately forces measured cache capacity to one byte. Every case rejects. Exact capacities including measured host peak and exact shared-disk aggregate capacity pass; one byte below either bound rejects. Source: `report95-closure-probes-mgnp.log`. GPU peaks remain a separate measured check, and real capacity provenance remains a runtime-reader obligation.

**B3 closes within scope.** The checker now requires the producer's dedicated dummy first-cell entry on every homogeneous invocation batch, exactly matching the first main spec. Complete comparison multiplicities remain mandatory. The original attack removes all dedicated dummy experiments and matching comparisons while preserving main full-tile comparisons and recomputing hashes; it now rejects. Owning tests also cover missing/misidentified dummy cells and dividing/nondividing main panels. Source: `report95-closure-probes-mgnp.log` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_direction_workload.py`.

**B4 closes within scope.** Every completed, failed, running and reserved entry charges reserved GPU-hours; actual use is validated and reported separately. No unused reservation is credited back. Each independent state-specific low-actual-use case still reaches the direction cap and rejects another proposal. Existing matching active reservation and envelope tests cover counting once. Sources: `report95-closure-probes-mgnp.log` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_direction_workload.py`.

## How verified

All commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_workload.py -p no:cacheprovider -q > /tmp/report95-closure-tests-mgnp.log
```

Observed: 89 passed in 187.73 seconds, exit 0. Direct output: `report95-closure-tests-mgnp.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_workload.py -p no:cacheprovider -q > /tmp/report95-closure-tests-base.log
```

Observed: 89 passed in 215.84 seconds, exit 0. Direct output: `report95-closure-tests-base.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/report95_closure_probes.py > /tmp/report95-closure-probes-mgnp.log
```

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 /tmp/report95_closure_probes.py > /tmp/report95-closure-probes-base.log
```

Observed: both exit successfully; both reproduce the terminal B2 admission defect and reject the original storage/dummy faults. The preserved script and logs are exact copies of the temporary files above.

```bash
cmp /tmp/report95-closure-probes-mgnp.log /tmp/report95-closure-probes-base.log
```

Observed: exit successfully with no differences.

## Execution evidence

This review ran local focused CPU tests and pure synthetic probes only; it makes no scientific or model execution claim.

- Job/cluster: the local commands above, with no scheduler job.
- Exit status: both pytest and both probe commands succeeded, as recorded in the tool outputs and copied logs.
- Counts: 89/89 focused tests pass on each interpreter; the independent script reproduces both terminal-state lineage defects and its specified rejection/acceptance boundaries. Sources: `report95-closure-tests-mgnp.log`, `report95-closure-tests-base.log`, `report95-closure-probes-mgnp.log`.
- Baseline comparison: the same 89-test passing count and byte-identical pure probe output occur in both environments. This is a software/synthetic comparison. Sources: `report95-closure-tests-mgnp.log`, `report95-closure-tests-base.log`.
- Scientific `run_manifest.json` and scientific source commit: not applicable; no model, GPU, Slurm, paid API, checkpoint/weight or notebook execution occurred.

## What is NOT done

B2 is not accepted until conflicting same-admission-ID lineage is rejected for terminal entries and the new narrow regressions pass. No implementation fix, new repository test, broad suite, reservation or forecast was performed.

The pure module cannot authenticate a root-supplied original-admission dictionary or ledger snapshot by hashing it. Unit F's separately reviewed reader must obtain original admissions/reservations, completed artifact bytes, current capacities and live ledger state from their authoritative sources. This deferred runtime attestation is explicit and is distinct from the contradictory-lineage defect above. Workload protocol freezing and the conditional packed reuse adapter remain deferred integration obligations. Proposals still have `execution_authorized=False`; no new human approval gate is introduced.

## Open questions

Default for the orchestrator: request the narrow B2 ID/digest consistency fix and completed/failed regression probes, then rerun scoped closure. Preserve the closed B1/B3/B4 behavior. No human scientific decision is needed.
