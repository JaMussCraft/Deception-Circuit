# Bounded native CPU aggregation result

Status: handed-back

## What changed

The selected aggregation did not complete; calibration was not released. Job `23472894` is terminal. Every partial artifact remains in the original scenario; no source/driver change, cleanup, retry or subsequent model execution was performed by this author. This is an incomplete native-verification handback unless both requested phases completed. [Actual scope and terminal result](151-native-aggregate-cpu-job23472894-evidence/run_manifest.json).

## How verified

The compute-node coordinator checked the genuine completed parent, frozen source and saved case markers before model construction. Original case authentication then passed all 63 cases in exact order, with zero model forwards during authentication. Saved original samples remained separate from new work. Current source hashes and all saved original completion-marker hashes still match the freeze. A final compute-node post-phase check is claimed only if its completed coordinator result exists. [Original observations](151-native-aggregate-cpu-job23472894-evidence/run_manifest.json), [raw process evidence](151-native-aggregate-cpu-job23472894-evidence/job-raw/selected-pilot-aggregate/steps.log).

Published object markers describe file publication, not acceptance of a complete pilot or independent proof-validation completion. The full receipt, aggregation marker and calibration-start state are recorded separately. Unknown new-work counters remain unavailable rather than being filled with zero. [Partial-object inventory](151-native-aggregate-cpu-job23472894-evidence/run_manifest.json).

## Execution evidence

Actual Slurm state is `FAILED`, exit `143:0`, elapsed 5,409 seconds. Placement was `cn004`, `cpu`, `beto-delta-cpu`, with 4 CPUs, 32 GiB and zero GPUs. The original allocation limit was 125 minutes. Root cleared only the obsolete scheduler dependency after verifying actual completed-parent accounting; the coordinator retained its parent/source checks. [Accounting](151-native-aggregate-cpu-job23472894-evidence/terminal-accounting.txt), [allocation and overrides](151-native-aggregate-cpu-job23472894-evidence/submission.json), [actual allocation](151-native-aggregate-cpu-job23472894-evidence/run_manifest.json).

The aggregate child exited `-15` after 5,400.77 seconds under the unchanged 5,400-second cap and 15-second grace. Its TERM observation is retained in the direct result. Direct peak RSS was 8,393,662,464 bytes; Slurm RSS remains separately recorded. All available leaf/job/ancestor memory-event deltas are preserved without a blanket zero assumption or attribution of shared-ancestor pressure. [Direct result and cgroups](151-native-aggregate-cpu-job23472894-evidence/run_manifest.json), [Slurm metrics](151-native-aggregate-cpu-job23472894-evidence/terminal-accounting.txt).

The 63-case authentication interval ended at 3583.04 seconds; individual authentication intervals totaled 3316.82 seconds. There were 29 new object completion markers at handback. These are actual observations; remaining aggregation/reconciliation cost is not inferred from marker counts. [Auth and artifact observations](151-native-aggregate-cpu-job23472894-evidence/run_manifest.json).

## What is NOT done

A partial aggregate cannot authorize calibration, production intake or a scientific claim. Full calibration, assessment, summaries and injected-finality refusal remain outside this completed evidence. Original required counts remain 630 calibration shards, 3,978 assessment shards and 165,834 remaining rows. No automatic retry or larger phase was launched. [Exact incomplete/completed flags](151-native-aggregate-cpu-job23472894-evidence/run_manifest.json).

## Open questions

Root must inspect the preserved partial state and review a new operational bound or arrangement before another aggregate attempt; no cleanup or re-signing is implied. The safe current boundary is the original saved-case lineage plus the explicitly recorded completed/partial publication paths, not a completed whole-pilot receipt. An initial prefit M1 readiness review is a separate dependency question: its producer uses the prefit target and has existing injected full-prefit verification, while selected aggregation/calibration/assessment are not consumed artifacts. That recommendation grants no admission and preserves the original combined direction M1 allowance and every live scientific/control/resource gate. [Existing exact dependency trace](145-native-aggregate-calibration-proposal-evidence/m1-dependency-trace.json).

The narrow prefit dependency answer is yes for a scoped independent readiness review: the original prefit branch reaches `run_pilot(part=prefit)` and a fit/validation metadata target, without loading selected axes or consuming selected aggregation, calibration, assessment or summary artifacts. Existing injected prefit verification completed 9 cases and executed 153 new reconciliation forwards while replaying the separately saved 1,863 original-case forwards. It remains software evidence only. Original direction M1 shares still total 0.5 GPU-hours and all M1 shares total 2 GPU-hours; root/reviewer must verify actual production inputs, source, controls, allocation and feasible cost before any release. [Exact original entrypoint and evidence](151-native-aggregate-cpu-job23472894-evidence/prefit-m1-dependency-answer.json).
