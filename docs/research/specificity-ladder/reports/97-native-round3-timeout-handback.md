# Native CPU verification stopped at case authentication

Status: handed-back

## What changed

Continued the authorized fresh CPU scenario on the reviewed frozen source. Production, harness, numerical kernels, inventories and source lineage remain unchanged. External process supervision and diagnostics are preserved separately from all pilot evidence. The full verification remains incomplete. [Source closure and latest evidence](97-native-round3-onecase-evidence/run_manifest.json).

## How verified

The earlier instrumented crash is localized by its preserved core: the faulting thread is Python's periodic traceback dumper, with `dump_frame` followed by `_Py_DumpTracebackThreads` and `faulthandler_thread`. A model-free check of the exact wrapper function passes with distinct original callables, excluding the suspected late-binding/recursion error in that wrapper. This identifies the faulting instrumentation thread; it does not establish a model-kernel defect or a minimal crash reproducer. [Exact C traceback](97-native-round3-onecase-evidence/gdb-python-only.log), [executable wrapper regression](97-native-round3-onecase-evidence/wrapper-regression.py), [core metadata and limitations](97-native-round3-onecase-evidence/run_manifest.json).

The released retry changed only recurring traceback dumping to fatal-handler-only support. Passive step logs, direct child RSS/process samples, thread limits and the original scenario checks remained. Completion-marker byte membership and hashes of the published case and its numeric child were checked without model execution. These byte checks are separate from the unfinished full semantic case authentication. [Instrumentation diff](97-native-round3-onecase-evidence/instrumentation-only.diff), [published state](97-native-round3-onecase-evidence/published-case-state.json).

## Execution evidence

CPU fixture execution only; scheduler job/cluster not applicable. The fresh scenario completed 9 prefit cases, 48 fit-capture pieces, 9 fit records, 210 validation shards and 9 selected records. The selection has 8,392 numeric files. The earlier timeout manifest's nonrecursive numeric-file count is explicitly corrected in the latest manifest while the original is preserved. [Completed scope](97-native-round3-onecase-evidence/run_manifest.json).

The first selected-pilot chunk reached its 600-second limit plus kill grace and exited 137. The subsequent read-only diagnostic reached the pre-forward boundary at 554.80 seconds without model forwards or scientific publication. [Preserved first failure and read-only diagnostic](97-native-round3-timeout-evidence/run_manifest.json).

In the fatal-handler-only retry, startup before `_pilot_invocation` was 583.17 seconds. That invocation returned after 59.28 seconds and 11,100 observed genuine forward calls. The durable case records 102.63 seconds of original case work, including its actual binding/construction work. These measurements remain authoritative original case evidence; no aggregation was executed. [Actual timings and case counters](97-native-round3-onecase-evidence/run_manifest.json), [original case summary](97-native-round3-onecase-evidence/published-case-state.json).

The process did not complete authentication within its 900-second cap. TERM was sent at 900.11 seconds; the child exited on SIGTERM with code -15 after 911.64 seconds, inside the allowed grace. `_numeric_backing_proof` returned at 885.75 seconds after 183.25 seconds, but the enclosing proof constructor and `_read_pilot_case` had not returned. Peak child RSS was 6,799,953,920 bytes. All observed leaf and ancestor memory-event deltas were zero, including OOM and OOM-kill events. [Direct child result](97-native-round3-onecase-evidence/selected-onecase-02-no-periodic/result.json), [step log](97-native-round3-onecase-evidence/selected-onecase-02-no-periodic/steps.log), [resource reconciliation](97-native-round3-onecase-evidence/run_manifest.json).

## What is NOT done

The published case is byte-complete but has no completed semantic-authentication/process claim. The pilot aggregate, calibration, assessment, calibration summary, full summary and final injected-lineage refusal remain unexecuted for this fresh full scenario. No whole-unit acceptance, scientific result or production admission is claimed. The original timeout, instrument crash, core and later timeout remain preserved. All owned processes are terminal; no automatic rerun or source modification followed either bounded failure.

## Open questions

The safe boundary is the existing published case identified in the raw state manifest. Any released continuation must authenticate it through the unchanged original path and retain its original numeric timings/counters, without re-execution or re-signing. Its scratch directory is empty. The measured limit is insufficient even for a complete case process, so no larger chunk is supported by this evidence. Root should review the already-proposed test-only prepared-context arrangement or another explicit operational bound before further heavy verification. No such repair or additional run was implemented or launched.
