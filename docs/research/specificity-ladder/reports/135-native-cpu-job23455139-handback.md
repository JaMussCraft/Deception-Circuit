# Slurm CPU native continuation completed

Status: handed-back

## What changed

Moved the authorized next native-verification chunk to a genuine Delta CPU allocation. Original contiguous cases 5–11 completed in one unchanged `pilot_cases` call. All original numerical execution, controls, publication and full case authentication ran; no aggregate or further chunk followed. The five earlier case references remain unchanged. [Complete result and scope](135-native-cpu-job23455139-evidence/run_manifest.json).

## How verified

The submitted driver manifest matches the frozen reviewed files. Before fixture construction, both supervisor and coordinator independently read the actual current Slurm allocation and checked job/user/node/work directory, CPU resources, absence of GPUs and finish time. Slurm allocation variables were retained unchanged. Final source/model/scenario checks passed inside the compute-node job. The local author follow-up read compact job metadata only and ran no local model or heavy verification.

The original injected fixture remains explicitly nonauthorizing, with `scientific_execution=False` and no production admission. Real `SLURM_JOB_ID` did not trigger production CUDA loading. Original case bundles were not rewritten to add job labels: separate immutable sidecars bind each new completed case byte reference to its actual allocation record, job/step/node/PID. Earlier login cases received no new job provenance. Sidecar publication/reference work is recorded separately. [Allocation facts](135-native-cpu-job23455139-evidence/coordinator-allocation.json), [driver/result](135-native-cpu-job23455139-evidence/coordinator-result.json), [per-case provenance](135-native-cpu-job23455139-evidence/per-case-observations.json).

## Execution evidence

Job 23455139 on cluster `delta` completed with exit `0:0` in 1,210 seconds, from `00:33:25` to `00:53:35 UTC`. It ran on cn002 in `cpu-interactive`, under `bjhz-delta-cpu`, with 4 CPUs, 32 GiB and zero GPUs. Actual submission retained the `projects` constraint and 45-minute allocation. [Terminal accounting](135-native-cpu-job23455139-evidence/terminal-accounting.txt), [submission](135-native-cpu-job23455139-evidence/submission.json).

The direct model-fixture child exited successfully after 1,204.23 seconds, with no timeout signal under the 2,400-second cap plus 15-second grace. Original native case timers and full authentication timings are separate observed intervals; the native interval is contained in the original case-work timer. All values below are compute-node observations, not relabeled login results. [Direct child result](135-native-cpu-job23455139-evidence/result.json), [per-case observations](135-native-cpu-job23455139-evidence/per-case-observations.json).

| Case | Source | Native seconds | Original case seconds | Full authentication seconds | Actual forwards |
|---|---|---:|---:|---:|---:|
| 5 | IOI calibration | 1.76 | 27.41 | 159.51 | 195 |
| 6 | MMLU calibration | 2.93 | 26.57 | 57.33 | 726 |
| 7 | FAR | 45.32 | 70.69 | 65.31 | 11,100 |
| 8 | FAR | 45.16 | 69.93 | 58.65 | 11,100 |
| 9 | IOI | 4.36 | 28.52 | 58.67 | 1,110 |
| 10 | MMLU | 15.54 | 42.07 | 61.19 | 4,246 |
| 11 | FAR calibration | 8.31 | 31.99 | 66.09 | 1,950 |

Total genuine new forwards were 30,427; authentication added none and had no forbidden call. The first case constructed a fresh process-local selected backing cache; later cases retained original cache-hit reference/source/PID and fresh byte-witness checks. No cache crossed a restart. [Actual counters and events](135-native-cpu-job23455139-evidence/run_manifest.json).

Direct child peak RSS was 6,888,169,472 bytes. Slurm independently reports step MaxRSS `7252296K`; these measurements are retained separately. The job and step-user cgroups enforced 34,359,738,368 bytes. Every available job/step/ancestor memory-event counter was unchanged; unavailable root counters are explicitly marked unavailable. [Direct resource result](135-native-cpu-job23455139-evidence/result.json), [terminal accounting](135-native-cpu-job23455139-evidence/terminal-accounting.txt), [cgroup reconciliation](135-native-cpu-job23455139-evidence/run_manifest.json).

## What is NOT done

The scenario now has 12 authenticated cases out of the original required 63; 51 remain. Full pilot aggregation, calibration scoring, assessment, summaries and injected-finality refusal remain unexecuted. No whole-unit acceptance, scientific result or allocated-GPU cost claim is made. The compute-node timings do not establish a controlled speed comparison or a bound for another workload/host. Original source/harness, all scientific counts, earlier failures and old timing records remain intact. [Current scope](135-native-cpu-job23455139-evidence/run_manifest.json).

## Open questions

Root owns state/accounting updates and any next CPU submission. Further long verification should use actual CPU allocations with the same provenance and preservation checks. This author submitted or retried no job and launched no subsequent chunk. The job, step and all owned child processes are terminal.
