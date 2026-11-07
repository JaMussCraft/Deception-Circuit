# Bounded native case and same-process authentication

Status: handed-back

## What changed

Executed the reviewed external coordinator against the unchanged frozen tiny CPU scenario. Exactly one new selected-pilot case completed through the original numerical producer, publication and authentication APIs. The same process then performed original full read-only authentication of that case with forwards, pilot execution and publication trapped. The earlier authenticated case was preserved. No subsequent case or aggregate was launched. [Exact commands, source closure and outcome](126-native-next-case-evidence/run_manifest.json).

## How verified

The coordinator verified scenario/source/model identity, read the completed selection, rebuilt and compared the original inventory, and preserved the exact complete case order. The original case API independently validated the inventory again, loaded its own axes and checked the completed result. Final source/model/backing checks passed. Original operation samples, own-source controls and timers remain in the genuine case artifact; no timing was copied or re-signed.

The passive outer forward count equals the original case counter. Same-process read-only authentication returned with no forbidden call, no new forward, and identical new-case bytes. The old case's complete tree also matches its earlier authenticated snapshot in hashes, sizes, modes, inode and modification time. Both completion markers of the new case were independently checked afterward. [Case evidence](126-native-next-case-evidence/new-case-summary.json), [original coordinator result](126-native-next-case-evidence/coordinator-result.json), [source snapshot](126-native-next-case-evidence/source_snapshot.json).

## Execution evidence

CPU tiny-fixture execution only; scheduler job/cluster not applicable. The child exited successfully after 758.48 seconds, with no timeout signal under its 1,200-second cap and 15-second kill grace. It entered the native invocation after 406.61 seconds. The native invocation took 65.40 seconds and made 11,100 actual forwards. [Direct child result](126-native-next-case-evidence/result.json), [phase timings](126-native-next-case-evidence/run_manifest.json).

The original case record retains 94.28 seconds of actual case work, including its native invocation and measured metadata/reference construction. The post-native window through publication and first complete authentication was 204.85 seconds; that is a combined window, not a separately measured pure authentication timer. All 11,040 original operation-timing samples, 10 positive-batch timings and 20 positive-control rows remain preserved and valid. [Original record summary](126-native-next-case-evidence/new-case-summary.json), [observed intervals](126-native-next-case-evidence/run_manifest.json).

Same-process full read-only authentication took 67.55 seconds, with zero additional forwards and zero forbidden calls. The process-local selected numeric cache was present; original cache-hit reference-byte and file-witness checks still executed. This measurement includes fresh validation work and is kept separate from the original numerical timings. It is not an isolated measurement of filesystem-cache effects. [Coordinator result](126-native-next-case-evidence/coordinator-result.json), [steps](126-native-next-case-evidence/steps.log).

Peak child RSS was 6,832,529,408 bytes. The enclosing finite user-slice maximum was 40,320,217,088 bytes, with 31,519,330,304 bytes of headroom before launch. Leaf and all observed ancestor memory-event deltas were zero, including OOM/kill events. These are observed login-host CPU/resource measurements, not an allocated-host startup or cold-filesystem bound. [Direct resource result](126-native-next-case-evidence/result.json), [before](126-native-next-case-evidence/memory-before.json), [after](126-native-next-case-evidence/memory-after.json), [reconciliation](126-native-next-case-evidence/run_manifest.json).

## What is NOT done

The scenario now has 2 authenticated selected cases out of the required 63; 61 remain. Full pilot aggregation, calibration, assessment, summaries and injected-finality refusal remain unexecuted for this fresh scenario. No whole-unit acceptance, scientific result or production admission is claimed. The original bounded failures and core remain preserved. Production/harness source and scientific counts are unchanged. [Current scope](126-native-next-case-evidence/run_manifest.json).

## Open questions

Root can use the measured same-process authentication cost when reviewing another bounded chunk. Every fresh process still pays its own construction and first validation costs; warm-cache validator objects cannot cross restart. Full aggregation must authenticate the complete original set and execute the original reconciliation and complete dependency checks. Its duration remains a separate gate. All owned processes are terminal, and this author launched no further attempt.
