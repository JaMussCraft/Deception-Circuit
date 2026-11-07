# Slurm CPU native cases completed

Status: handed-back

## What changed

Original contiguous cases 12–31 completed in one unchanged `pilot_cases` call on a genuine CPU allocation. Every case ran original numerical execution, controls, publication and full authentication. The 12 prior case references remain unchanged. No aggregate or further chunk followed. [Scope and complete result](137-native-cpu-job23458182-evidence/run_manifest.json).

## How verified

Supervisor and coordinator independently authenticated the real current Slurm allocation before fixture construction. They retained allocation environment variables and checked user, node, working directory, CPU resources, absence of GPUs and finish time. Final scenario/model and frozen-source checks passed on the compute node. Local follow-up read compact metadata only and performed no model or full proof rerun. [Allocation](137-native-cpu-job23458182-evidence/coordinator-allocation.json), [observed checks](137-native-cpu-job23458182-evidence/steps.log), [source and driver closure](137-native-cpu-job23458182-evidence/run_manifest.json).

Separate immutable sidecars bind each completed case byte reference to the actual job, step, node, PID and allocation record. They preserve original numeric/authentication timers and measure sidecar publication separately. Earlier cases were not relabeled. The fixture remains injected, `scientific_execution=False` and nonauthorizing. Process-local numeric backing was constructed on the first authentication and reused only through existing original checks within this process. [Per-case provenance](137-native-cpu-job23458182-evidence/per-case-observations.json), [original coordinator result](137-native-cpu-job23458182-evidence/coordinator-result.json).

## Execution evidence

Job 23458182 completed with exit `0:0` in 1,915 seconds, from `02:18:10` to `02:50:05 UTC`. It ran on cn001 in `cpu-interactive`, under `bjhz-delta-cpu`, with 4 CPUs, 32 GiB and zero GPUs. The submission retained the `projects` constraint and 59-minute allocation. All job steps are terminal and successful. [Terminal accounting](137-native-cpu-job23458182-evidence/terminal-accounting.txt), [submission](137-native-cpu-job23458182-evidence/submission.json).

The direct fixture child exited successfully after 1,909.40 seconds, without a timeout signal under the 3,300-second cap plus 15-second grace. Setup through first native invocation took 311.58 seconds. The native interval below is contained within the original case-work timer; authentication is separate actual work. These are compute-node observations. [Direct child](137-native-cpu-job23458182-evidence/result.json), [timing summary](137-native-cpu-job23458182-evidence/timing-summary.json), [per-case observations](137-native-cpu-job23458182-evidence/per-case-observations.json).

| Case | Source | Native seconds | Original case seconds | Full authentication seconds | Actual forwards |
|---|---|---:|---:|---:|---:|
| 12 | ioi calibration | 1.56 | 22.27 | 124.46 | 195 |
| 13 | mmlu calibration | 2.92 | 23.15 | 47.41 | 726 |
| 14 | far_v2 | 45.39 | 65.42 | 46.24 | 11,100 |
| 15 | far_v2 | 45.50 | 65.49 | 47.07 | 11,100 |
| 16 | ioi | 4.37 | 25.19 | 45.74 | 1,110 |
| 17 | mmlu | 15.80 | 34.23 | 45.81 | 4,246 |
| 18 | far_v2 calibration | 8.33 | 26.70 | 42.95 | 1,950 |
| 19 | ioi calibration | 0.98 | 19.01 | 39.30 | 195 |
| 20 | mmlu calibration | 2.99 | 18.86 | 40.82 | 726 |
| 21 | sdr_v2 | 47.77 | 64.15 | 39.76 | 11,100 |
| 22 | sdr_v2 | 47.07 | 63.01 | 35.03 | 11,100 |
| 23 | ioi | 4.45 | 19.25 | 35.04 | 1,110 |
| 24 | mmlu | 16.35 | 30.81 | 33.79 | 4,246 |
| 25 | sdr_v2 calibration | 8.69 | 23.25 | 33.02 | 1,950 |
| 26 | ioi calibration | 0.97 | 15.25 | 33.97 | 195 |
| 27 | mmlu calibration | 2.89 | 16.82 | 34.54 | 726 |
| 28 | sdr_v2 | 46.35 | 60.67 | 34.71 | 11,100 |
| 29 | sdr_v2 | 46.67 | 62.28 | 36.90 | 11,100 |
| 30 | ioi | 4.45 | 19.60 | 35.05 | 1,110 |
| 31 | mmlu | 16.29 | 32.49 | 35.98 | 4,246 |

Genuine new forwards totaled 89,331. Full authentication added none and had no forbidden forward call. The first authentication took 124.46 seconds; later authentications ranged from 33.02 to 47.41 seconds. Here fresh construction concerns the process-local numeric backing, without a claim of cold filesystem caches. [Actual counters and timings](137-native-cpu-job23458182-evidence/run_manifest.json).

Direct child peak RSS was 6,887,251,968 bytes. Slurm independently reports step MaxRSS `7776884K`; these measurements remain separate. Job and step-user cgroups enforced 34,359,738,368 bytes. Every available job/step/ancestor memory-event counter was unchanged; root counters remain explicitly unavailable. [Direct resource result](137-native-cpu-job23458182-evidence/result.json), [terminal accounting](137-native-cpu-job23458182-evidence/terminal-accounting.txt), [cgroup reconciliation](137-native-cpu-job23458182-evidence/run_manifest.json).

## What is NOT done

The scenario has 32 authenticated cases out of 63; 31 remain. Full pilot aggregation, calibration scoring, assessment, summaries and injected-finality refusal remain unexecuted. No full-unit acceptance, scientific result, allocated-GPU cost claim or controlled host-speed comparison is made. Source/harness, original scientific counts, earlier failures and timing records remain intact. [Current scope](137-native-cpu-job23458182-evidence/run_manifest.json).

## Open questions

Root owns state/accounting and any next CPU submission. A remaining-scope proposal may use these observed timings, with an explicit bound and buffer, after this handback. No further model execution or submission is authorized by this report.
