# Final native CPU case continuation proposal

Status: handed-back

## What changed

Propose original cases 49–62 in one unchanged `pilot_cases` call, preserving the expected 49 prior cases. This is a conditional job: its launcher requires `afterok:23470779`, and a read-only gate requires genuine successful parent completion before model construction. Successful case execution would finish the case inventory, while pilot aggregation remains separate. [Scope and limits](proposal.json).

## How verified

The parent gate checks actual Slurm accounting, completed process and coordinator results, exact ordered parent case coverage, forward/control reconciliation, prior-case preservation, source/catalogue/driver identity and pinned scenario/tiny-model bytes. It compares the parent’s stored case references with the original coordinator’s existing reference map and checks allocation sidecars. It adds no second case-byte scan or numerical proof replay. Any missing, changed or incomplete parent evidence refuses before model construction. [Gate](parent_gate.py), [pinned inputs](parent-expectation.json), [coordinator changes](accepted-driver.diff).

Accounting may take up to 30 seconds to become visible after `afterok`; observations and actual gate time are retained. A failed terminal parent refuses immediately. The gate cannot convert a running process or partial case into completion, and its evidence remains nonauthorizing. [Implementation](parent_gate.py), [focused checks](protocol-checks.json).

The model-free tests first demonstrated 12 failures with absent gate behavior. Final focused checks passed 15 tests in each supported interpreter, with BLAS/OMP/MKL threads set to one and the pytest cache disabled. Syntax compilation and shell syntax checks passed; source hashes remain unchanged. No local model or heavy test was run. [Red evidence](red-base.log), [base checks](final-green-base.log), [mgnp checks](final-green-mgnp.log), [protocol checks](protocol-checks.json).

## Execution evidence

The derived earlier buffered envelope is 2,436.33 seconds. This proposal explicitly adds 60 seconds for the new gate: a bounded accounting wait plus metadata work allowance, producing 2,496.33 seconds. Request a 2,520-second child cap plus 15-second grace within a 44-minute Slurm allocation. The outer margin is 105 seconds. These are planning allowances; actual gate time will be measured separately and no new timing is presented as observed. [Cost envelope](proposal.json), [resource checks](protocol-checks.json).

Use `cpu-interactive`, `bjhz-delta-cpu`, `projects`, 4 CPUs, 32 GiB and zero GPUs, requiring 16 GiB finite ancestor headroom. Preserve real Slurm environment variables and immutable allocation sidecars. The parent’s result is checked independently of the dependency directive. [Launcher](launch.sbatch), [unchanged allocation helper](allocation_facts.py), [static checks](protocol-checks.json).

## What is NOT done

No model case, job submission, retry, source/harness modification, receipt re-signing, aggregate, calibration or assessment has occurred in this proposal. Full case coverage will require the genuine successful execution of both parent and final jobs. Completing the selected cases alone does not complete the whole native pilot or authorize scientific execution.

## Open questions

Root reviews the exact frozen manifest and submits with the explicit dependency. On any failure, preserve all artifacts and stop. Report the final job under report141 with actual case/authentication/publication/gate/resource timings. Pilot aggregation remains a separate bounded step after full case coverage is authenticated.
