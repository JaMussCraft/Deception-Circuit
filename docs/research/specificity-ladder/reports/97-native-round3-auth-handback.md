# Existing selected-case authentication

Status: handed-back

## What changed

Authenticated the existing published selected case through the original `_read_pilot_case` and `_CompletedPackingProof` path. The native case was not re-executed, and its receipts were not re-signed or rewritten. Production and harness source remain frozen. All earlier bounded failures and the instrument core remain preserved. [Exact source and execution manifest](97-native-round3-auth-evidence/run_manifest.json), [prior handback](97-native-round3-timeout-handback.md).

## How verified

Independently checked the stored full tiny-model state/config and source identity, read the completed selection, rebuilt and compared the canonical inventory, and validated its entire expected invocation list before choosing the existing case. The expected first invocation ID matched the published directory. Then the unchanged proof path authenticated numerical backing, scope, original measured evidence and own-source controls.

Pilot execution, model forwards and scientific publication/write entry points were trapped. The exact case tree before and after authentication matched in bytes, hashes, modes, inode and modification time. Final model/backing and frozen-source checks also passed. [Read-only driver](97-native-round3-auth-evidence/report97-native-existing-case-auth.py), [before](97-native-round3-auth-evidence/case-before.json), [after](97-native-round3-auth-evidence/case-after.json), [raw steps](97-native-round3-auth-evidence/steps.log).

## Execution evidence

CPU fixture authentication only; scheduler job/cluster not applicable. The child exited successfully after 507.40 seconds, with no timeout signal. The original full case-authentication call took 186.89 seconds. Peak child RSS was 6,805,737,472 bytes. The configured process cap was 900 seconds with 15 seconds of kill grace. All observed leaf and ancestor memory-event deltas were zero. These are observed login-host measurements with fresh process-local construction; filesystem caches and allocated-host portability are not asserted. [Direct process result](97-native-round3-auth-evidence/result.json), [resource provenance and reconciliation](97-native-round3-auth-evidence/run_manifest.json).

Exactly 1 of the required 63 selected cases is authenticated; 62 remain. New model forwards, pilot-execution calls and publication calls were all zero. The original case still records 102.63 seconds and 11,100 genuine forward calls, kept separate from this new authentication work. [Completion event and original counters](97-native-round3-auth-evidence/run_manifest.json).

## What is NOT done

No additional native case, full selected-pilot aggregation, calibration, assessment, summaries or final injected-lineage refusal was executed. The full native verification and whole-unit acceptance remain incomplete. No production admission or cross-host startup bound follows from this authentication result.

## Open questions

The authenticated case is preserved at the exact path recorded in the manifest. Further native execution requires a separately released operational plan; this isolated authentication result does not establish a safe larger chunk. No additional run was launched. All owned processes are terminal.
