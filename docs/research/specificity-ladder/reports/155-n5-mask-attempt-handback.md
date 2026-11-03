# Actual N5 mask attempt

Status: handed-back

## What changed

The sole approved replacement attempt ended incomplete at its fixed finish boundary. It produced no complete pilot receipt and cannot authorize mask M5 work. Original and replacement requested charges remain retained; no retry occurred. [Actual run manifest](155-n5-mask-attempt-evidence/run_manifest.json)

## How verified

Read actual Slurm terminal accounting, the unchanged launcher events/application log, post-terminal completion markers and the reconciled canonical reservation. Both objective arms published timing validation/checkpoint/selection objects. FAR and SDR timing H-banks completed; the final pilot receipt is absent. Partial artifacts remain in their original namespace. No assessment effects were inspected. [Terminal accounting](155-n5-mask-attempt-evidence/terminal-accounting.txt), [launcher events](155-n5-mask-attempt-evidence/terminal-launch-events.jsonl)

## Execution evidence

The job was FAILED with exit status `1:0` on the actual single H200 allocation. The controller sent TERM for `fixed_finish_reserve` and raised `TimeoutError`; no earlier numerical-control or out-of-memory exception was observed. This was the planned bounded stop, not a successful calibration. [Application/launcher output](155-n5-mask-attempt-evidence/terminal-slurm.log)

| [Actual attempt](155-n5-mask-attempt-evidence/run_manifest.json) quantity | Value |
|---|---:|
| Actual elapsed seconds | 2342 |
| Original requested minutes | 45 |
| Replacement reserved GPU-hours retained | 0.75 |
| Cancelled original reserved GPU-hours retained | 0.75 |
| Cumulative mask M1 reserved GPU-hours | 1.5 |
| GPUs | 1 |
| CPUs | 4 |
| Host RAM, GiB | 64 |

The reconciled reservation remains failed with its full requested charge. Neither the unused time nor partial validation artifacts refund an attempt. Timing-only H-banks/checkpoints cannot be relabelled as scientific training or complete calibration evidence.

## What is NOT done

No complete calibrated mask cost proof or scientific mask result exists from this attempt. The failed job cannot enter the completed-pilot intake or admit M5. No scientific null, numerical failure, successful specificity claim, source change, shortened control panel, extension or second attempt is inferred.

## Open questions

Any further mask execution needs an applicable separately authorized path; the approved one-replacement allowance is consumed. Preserve all partial evidence for read-only diagnosis. The separately planned A2 scoring packet does not depend on treating this attempt as successful.
