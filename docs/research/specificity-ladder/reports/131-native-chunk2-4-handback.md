# Bounded original native chunk completed

Status: handed-back

## What changed

Executed exactly the accepted contiguous cases in one original `pilot_cases` call against the unchanged frozen tiny CPU scenario. Each case completed original numerical execution, durable publication and full authentication. The two existing case references remain unchanged. No aggregate, next chunk or retry was run. [Command, complete result and source closure](131-native-chunk2-4-evidence/run_manifest.json).

## How verified

The coordinator refreshed source/model/scenario identity, rebuilt and compared the original complete inventory and verified its exact case order. The original API independently validated inventory again and loaded its own selected axes. Passive wrappers called each original numerical producer and case reader once, measured actual per-case work and rejected model forwards during authentication. Each original case counter equals its observed outer forward count; their sum equals the process count.

The first case constructed a fresh process-local selected numeric backing cache. Later cases used that original cache with current reference/PID/source checks and fresh byte witnesses. There was no cache transport, skipped proof, success-flag replay or receipt re-signing. Final model/source/backing checks and preserved-reference comparisons passed. New completion markers were independently checked after termination. [Per-case evidence](131-native-chunk2-4-evidence/per-case-observations.json), [preserved references](131-native-chunk2-4-evidence/preserved-references.json), [exact source snapshot](131-native-chunk2-4-evidence/source_snapshot.json).

## Execution evidence

CPU tiny-fixture execution only; scheduler job/cluster not applicable. The child exited successfully after 843.43 seconds, without a timeout signal under the 1,500-second cap plus 15-second kill grace. Numerics began after 361.68 seconds of source/model/inventory setup. [Direct child result](131-native-chunk2-4-evidence/result.json), [actual events](131-native-chunk2-4-evidence/run_manifest.json).

All table values are actual observations. The native interval is contained in the original case timer, which also includes its original metadata/reference construction. Authentication occurs separately after publication. [Per-case observations](131-native-chunk2-4-evidence/per-case-observations.json).

| Case | Source | Native seconds | Original case seconds | Full authentication seconds | Actual forwards |
|---|---|---:|---:|---:|---:|
| 2 | IOI | 7.50 | 31.00 | 181.12 | 1,110 |
| 3 | MMLU | 23.39 | 48.80 | 65.77 | 4,246 |
| 4 | FAR calibration pilot | 12.42 | 62.37 | 74.88 | 1,950 |

The process performed 7,306 genuine new forwards. All authentication forward counts and forbidden-call counts are zero. Original synchronized operation samples, positive-batch timers and actual positive-control rows remain preserved in each completed case. The calibration-pilot case is validation timing work; no calibration scoring shard was executed. [Counts, timers and controls](131-native-chunk2-4-evidence/run_manifest.json).

Peak child RSS was 6,825,312,256 bytes. Finite ancestor headroom before launch was 31,910,047,744 bytes against a user-slice maximum of 40,320,217,088 bytes. Leaf and observed ancestor memory-event deltas were zero, including OOM/kill events. These are observed login CPU measurements and provide no allocated-host or cold-filesystem cost bound. [Direct resource result](131-native-chunk2-4-evidence/result.json), [before](131-native-chunk2-4-evidence/memory-before.json), [after](131-native-chunk2-4-evidence/memory-after.json), [event reconciliation](131-native-chunk2-4-evidence/run_manifest.json).

## What is NOT done

There are now 5 authenticated cases out of the original required 63; 58 remain. Whole-pilot aggregation, calibration, assessment, summaries and injected-finality refusal remain unexecuted for this fresh full scenario. No whole-unit acceptance, scientific result or production admission is claimed. Frozen source/harness, numerical kernels, profiles and scientific coverage are unchanged. All earlier bounded failures and the core remain preserved. [Current scope](131-native-chunk2-4-evidence/run_manifest.json).

## Open questions

Root can use these measured cold and same-process authentication costs when selecting another bounded physical chunk. Fresh processes still require original construction and authentication; the entire original case set and reconciliation remain mandatory before a completed pilot receipt. This author launched no further work. All owned processes are terminal.
