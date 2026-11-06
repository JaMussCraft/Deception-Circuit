# Independent genuine H100 timing and control audit

Status: handed-back

## What changed

Accepted the genuine original-H bank and prefix-only timing/control run under immutable source `50e947bb852613e3a270082651f2bd1b7bb0c525` and the existing frozen G3 receipt. This acceptance provides measured cost inputs and native control evidence; it does not admit full scoring or establish specificity. [Independent verdict](177-h100-timing-evidence/verdict.json), [execution provenance](177-h100-timing-evidence/run_manifest.json).

## How verified

Reviewed raw command, source, allocation, GPU, native completion, phase-publication and accounting evidence without reading an author outcome report. A dedicated CPU audit rehashed the fetched files, source and literal aliases, asserted exact project module origins, and required exact native numerical-environment equality before the owning bank reader. Original context/live, stage-manifest, typed bank, full prefix-key scope and positive-control validators passed. Native artifacts and the original CLI identify uninjected execution on the same H100 UUID in bfloat16. [Actual CPU result](177-h100-timing-evidence/executions/delta-r2-01/RESULT.json), [source provenance](177-h100-timing-evidence/run_manifest.json), [bank manifest](177-h100-timing-evidence/bank-run_manifest.json), [score manifest](177-h100-timing-evidence/score-run_manifest.json).

Both phases used fresh owning proofs from the same replacement CPU, followed by cache checks, root publication and timely consumption. The continuation preserves the original GPU job, configuration, placement and reservation. Historical captured ledger bytes authenticate entry; the reconciled current ledger separately retains the full reserved charge. [Phase chain](177-h100-timing-evidence/small-receipt-phase-chain.json), [native audit and reconciliation](177-h100-timing-evidence/executions/delta-r2-01/RESULT.json).

## Execution evidence

Bridges job 50189932 completed with exit `0:0` after 2260 seconds. Independent Delta CPU audit 23609718 completed with exit `0:0` after 85 seconds. The provenance names the full source commit above. [GPU accounting](177-h100-timing-evidence/GPU-scheduler-accounting.json), [CPU terminal confirmation](177-h100-timing-evidence/audit-terminal-accounting.json), [run_manifest.json](177-h100-timing-evidence/run_manifest.json).

Observed prefix rows 2484 equal expected 2484; observed positive controls 144 equal expected 144. Positive-control failures and invalid assay rows are 0. Observed maximum donor-logit recovery error 0 equals ideal recovery error 0; maximum empty/self-replay margin error 0 equals ideal no-op error 0. These are numerical baseline checks, not independent effect replication. The typed bank contains original-H train/validation sources, 400 per task, without assessment IDs. [Counts and baseline assertions](177-h100-timing-evidence/verdict.json), [owning-reader evidence](177-h100-timing-evidence/executions/delta-r2-01/RESULT.json).

Bank compute took 109.0288 seconds after a cold model load of 555.7061 seconds. Prefix score compute took 518.3888 seconds after a warm model load of 9.6033 seconds. Bank and score CLI elapsed times were 970.7687 and 638.8854 seconds; native stages exclude publication. GPU memory peaks include the resident model within measured compute scope. [Raw timing and memory](177-h100-timing-evidence/executions/delta-r2-01/RESULT.json), [rounded display derivation](177-h100-timing-evidence/timing-display.json).

## What is NOT done

No primary-effect values were selected, reported or aggregated; no assessment summary or specificity inference was produced. No full-score launch, source change, new GPU attempt or model execution by the reviewer. The original one-hour reservation remains charged despite shorter actual runtime. [Verdict and limits](177-h100-timing-evidence/verdict.json).

## Open questions

The structural full domain contains 59652 rows and 3396 positive controls. A row-ratio multiplication gives only a compute orientation, not a runtime bound. Full scoring still needs separately reviewed cost admission accounting for cold startup, changed operation/control mix, sequence lengths, aliases, source/input guards, potentially scaling artifact I/O, fresh CPU/cache/protection/budget transfers and finish reserve. The warm second load cannot substitute for cold-start evidence. [Structural counts](177-h100-timing-evidence/executions/delta-r2-01/RESULT.json), [complete cost inputs and limitations](177-h100-timing-evidence/timing-cost-inputs.json).
