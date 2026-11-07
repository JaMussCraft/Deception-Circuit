# Native continuation in a real Slurm CPU allocation

Status: UNEXECUTED. Root reviews, checks scheduler policy and submits. No long verification runs on login.

## Exact scope and resources

Advance original contiguous indices 5–11 in one original `pilot_cases` call, preserving all five completed cases. This gives 7 new cases and 12 authenticated cases if successful, out of the unchanged original 63. Profiles, inputs, numerical counts, callbacks and original publication/authentication remain unchanged. The chunk combines smaller IOI/MMLU calibration cases, full FAR cases, IOI/MMLU full cases and FAR calibration; no cells or controls are omitted. [Exact IDs/profiles](proposal.json).

Request one Delta CPU node/task, 4 CPUs, 32 GiB and no GPU. The proposed account is `bjhz-delta-cpu`, partition `cpu`, with `--constraint=projects`; root confirms scheduler policy with test-only. Keep numerical BLAS/OMP/MKL threads at one to preserve the existing profile. Process cap is 2,400 seconds plus 15-second kill grace; Slurm wall time is 45 minutes, below one hour. [Resources](proposal.json).

## Cost basis and uncertainty

Use prior **login** observations only as planning allowances: older setup 583.17 seconds, maximal observed original-case work 102.63 seconds for each new case, first cold authentication 186.89 seconds and maximal measured warm authentication 74.88 seconds for each subsequent case. Add chosen publication and final/exit allowances. The subtotal is 1,992.78 seconds; a 20% buffer gives 2,391.33 seconds, rounded up to 2,400. [Inputs/formula](proposal.json).

These are not compute-node measurements or an allocated-host bound. The first CPU-job outcome will retain its actual host/CPU, elapsed time, RSS, allocation limits, cgroup events and per-case native/authentication costs separately. Old login timing records remain untouched and are never labeled as newly executed in Slurm.

## Honest Slurm behavior

The coordinator uses original `verify_scenario`/`tiny_model`, inventory, `pilot_cases` and case-reader APIs. The explicit injected fixture flag remains true; `scientific_execution` and production admission remain false. It does not enter production `main`, the production CUDA loader or live GPU admission, and creates no fake allocation adapter. Actual `SLURM_JOB_ID` does not by itself promote authority. [Source findings](proposal.json).

Existing runtime producers use the real job ID wherever they already emit one. Individual original case bundles lack a job-ID field, so the driver adds separate immutable allocation/case-reference sidecars outside those bundles; it does not rewrite them. Each new sidecar binds the actual job/step/node/PID, a freshly read allocation record and the original completed case byte reference. Its actual publication/reference work is recorded separately. Old cases receive no new job provenance. [Coordinator](coordinator.py).

No Slurm allocation variable is unset, changed or spoofed. Before any fixture model starts, both supervisor and coordinator query the actual current `scontrol` record and verify user, RUNNING job, node, work directory, CPU account/partition, exact requested CPU/RAM resources, no allocated GPUs and a sufficient real finish deadline. GPU environment conflicts cause refusal rather than an environment workaround. CPU model identity is also checked after construction. [Resource reader](allocation_facts.py).

## Prepared launcher and commands

[launch.sbatch](launch.sbatch) uses an actual Slurm step with core binding. It does not source a GPU profile or alter allocation labels. Root-only scheduler checks/submission, **not performed by this author**:

```bash
sbatch --test-only .superpowers/sdd/plan-a3/native-continuation-plan/next-chunk-cpu-proposal/launch.sbatch
sbatch --parsable .superpowers/sdd/plan-a3/native-continuation-plan/next-chunk-cpu-proposal/launch.sbatch
```

Run from the worktree; the script and Slurm header also set its explicit absolute working directory. Root should check [driver-hashes.json](driver-hashes.json) and source closure before submission. Each actual job uses fresh `diagnostics/cpu-next-cases5-11-jobJOBID` outputs. The launcher refuses login use; no fixture runs before actual allocation checks.

## Capture, refusal and validation

The supervisor preserves the complete Slurm environment into the child and captures only allowlisted resource/provenance fields. It records actual allocation facts before/after, direct-child `wait4` wall/CPU/RSS, node affinity, cgroup path and leaf/ancestor memory limits/events. Both cgroup v1 and v2 are handled; unavailable event counters remain explicitly unavailable. It requires visible finite ancestor headroom before model work. Physical host RAM is not substituted for the allocated memory limit. Final Slurm job completion/accounting remains a later actual `sacct` observation, never an invented in-job success flag.

All old destinations must remain unchanged, all new destinations absent and scratch empty. Every original full case reader still executes, including fresh byte witnesses on cache hits. Only an actually constructed same-process cache is reused. On any failure or timeout preserve every output/checkpoint and stop; no automatic retry, overwrite, further chunk or aggregate.

Python compilation/AST protocol checks and Bash syntax checks pass; no script was imported/executed and no job command was run. All original source/harness hashes match the frozen manifest. [Checks](protocol-checks.json), [driver/source hashes](driver-hashes.json). This proposal remains nonauthorizing for production or GPU cost.
