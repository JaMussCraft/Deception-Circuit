# Larger native CPU continuation

Status: proposed, UNEXECUTED. Root accepted sizing in principle; exact code/hash review and submission remain root actions. No local model or heavy verification is run.

## Exact scope

Advance contiguous indices 12–31 in one original `pilot_cases` call, preserving all 12 prior cases. This adds 20 cases, reaching 32 of the original 63 if successful. No aggregate, additional chunk, control omission, original source/harness change or cache transport occurs. [Exact IDs and signature mapping](proposal.json).

The chunk finishes the remaining FAR cases, a complete SDR cycle and the following SDR selected-pilot own-source/IOI/MMLU panel, ending before calibration cases 32–34. New SDR own-source invocations match the measured generic paired-source physical geometry, operation mix, cell and batch-group counts; their actual timings remain unmeasured. All original semantic/source/control validators still run. [Next boundary](proposal.json).

## Compute-node timing basis

Use actual CPU job 23455139 rather than a login-time speed assumption: setup 359.24 seconds, first full authentication 159.51 seconds, and the maximal later full authentication 66.09 seconds. Map original case-work costs by identical cells, groups, operations, physical/model/source profile and MMLU-versus-paired-source branch, taking the observed maximum within each class. The mapped case-work total is 861.81 seconds. [Recorded CPU observations and exact mapping](proposal.json).

Observed original publication-window plus allocation-sidecar work peaked at 1.10 seconds; charge 2 seconds per case. Post-API checks and process exit took 16.31 seconds; charge 30 seconds. Including one cold and subsequent warm authentication gives 2,706.27 seconds. A 20% buffer gives 3,247.53 seconds, rounded up to a **3,300-second child cap plus 15-second kill grace**. [Actual publication/tail observations and calculation](proposal.json).

Slurm wall time is 59 minutes with 4 CPUs, 32 GiB, zero GPUs and `projects` constraint on `bjhz-delta-cpu`/`cpu-interactive`. This leaves 4 minutes outside the child cap. A larger next cut would need a 57-minute child allowance and leave only 2 minutes outside it; completing the next full calibration cycle reaches an hour before outer costs. The selected boundary retains cleanup/preflight margin while nearly tripling the previous chunk. These are bounded-trial allowances, not an empirical upper bound or allocated-GPU cost claim. [Sizing alternatives and resources](proposal.json).

## Existing safeguards retained

The new coordinator is only the accepted CPU driver with the contiguous selector changed and deadline allowance adjusted. All prior source/model/inventory and old-reference checks remain. The first proof constructs its own process-local backing cache; every later hit retains current PID/source/reference checks and fresh file witnesses. The actual CPU job/step/node environment remains untouched and independently checked through current Slurm facts. New immutable sidecars bind only the newly executed cases to their allocation, leaving old case bundles and timings intact.

The supervisor requires a real RUNNING CPU allocation on its actual node, exact CPU/RAM and no GPU, sufficient actual finish time, and finite cgroup headroom. It records direct-child wall/CPU/RSS plus actual allocation and v1/v2 cgroup counters. Missing counters stay unavailable. Any partial destination, mismatch, timeout or failure preserves all outputs and stops without clearing or retrying.

## Root-only commands

From the explicit worktree, after checking the final [hash manifest](driver-hashes.json):

```bash
sbatch --test-only .superpowers/sdd/plan-a3/native-continuation-plan/next-chunk-cpu12-31-proposal/launch.sbatch
sbatch --parsable .superpowers/sdd/plan-a3/native-continuation-plan/next-chunk-cpu12-31-proposal/launch.sbatch
```

The launcher uses one real CPU Slurm step and fresh `diagnostics/cpu-next-cases12-31-jobJOBID` outputs. Root sequences it after the current CPU audit; this author performs no scheduler test/submission. Final scientific execution/admission flags remain false.

## Verification and limits

Python AST/compilation, one-original-API/no-aggregate protocol checks and Bash syntax pass. No script was imported/executed. Original source hashes remain frozen. Exact diffs from the accepted CPU driver and all hashes are included for root review. [Checks](protocol-checks.json).

Future node/caches and new task inputs may change timing. Every actual original case, authentication, publication and resource measurement must remain visible and separate from these planning inputs. Full remaining pilot coverage, original reconciliation and later calibration/assessment/summary gates are unchanged.
